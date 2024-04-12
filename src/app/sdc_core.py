#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: Camera functionality
#
#    Copyright (c) 2016-2017, 2024, Camlab Project Team
#
#    Permission is hereby granted, free of charge, to any person
#    obtaining  a copy of this software and associated documentation
#    files (the "Software"), to deal in the Software without restriction,
#    including without limitation the rights to use, copy, modify, merge,
#    publish, distribute, sublicense, and/or sell copies of the Software,
#    and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
#    THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#-------------------------------------------------------------------------------

import os
import time
import threading
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal

import sys

from logger import logger as lg
import vframe
import gui

from udp import command_queue, Socket
 
iframe_event          = threading.Event()
vsthread_finish_event = threading.Event()

#-------------------------------------------------------------------------------
class SdcCore(QObject):

    frame_signal         = pyqtSignal( list  )
    display_frame_signal = pyqtSignal( int )
    
    #-------------------------------------------------------
    def __init__(self, parent):
        super().__init__()
        
        self.parent = parent

        #-----------------------------------------
        #
        #    MMR 
        #
        
        #-----------------------------------------
        #
        #    Video frame
        #
        self._pixmap = self.init_frame()
        self._roll_line = 1000
        self._k = 1
        self._queue_limit_exceed = False
        
        vframe.init_numpy()
        vframe.create_frame_pool()

        self._f = vframe.Vframe()
        vframe.reg_pyobject(iframe_event,          0)
        vframe.reg_pyobject(vsthread_finish_event, 1)

        class HookStub:
            def run(self, host):
                pass

        self.hook = HookStub()

        self._agc_ena     = False
        self._vstream_ena = False

        self._vstream_on  = False
        
        self.org_thres = 5
        self.top_thres = 5
        self.discard   = 0.005
        
        self._kf = 0.1
        self._kp = 0.5
        self._ka = 0.5
        
        self._stim = 0
        
        self._swing = 4096.0
        
        self.IEXP_MIN = 0
        self.IEXP_MAX = 978
        self.FEXP_MIN = 3
        self.FEXP_MAX = 1599
        
        self._iexp = self.IEXP_MIN
        self._fexp = self.FEXP_MIN
        
        self._top_ref = 3800.0;
        
        self.window_histo = np.zeros( (1024), dtype=np.uint32)
        self.fframe_histo = np.zeros( (1024), dtype=np.uint32)
        
        #-----------------------------------------
        #
        #    UDP socket
        #
        self._sock = Socket()

    #-------------------------------------------------------
    def deinit(self):
        self._sock.close()
    
    #-------------------------------------------------------
    def init_frame(self):
        return np.tile(np.arange(4095, step=32, dtype=np.uint16), [960, 10])
    
    #-------------------------------------------------------
    def agc_slot(self, checked):
        self._agc_ena = checked
        
    #-------------------------------------------------------
    def vstream_slot(self, checked):
        self._vstream_ena = checked

    #-------------------------------------------------------
    def generate(self):
        time.sleep(0.04)
        self._pmap = np.right_shift( self._pixmap, 4 ).astype(dtype=np.uint8)
        self._pmap[:, self._roll_line] = 255
        if self._roll_line < 1280-1:
            self._roll_line += 1
        else:
            self._roll_line = 0

        return self._pmap

    #-----------------------------------------------------------------
    #
    #    Video frame
    #
    #-------------------------------------------------------
    def init_cam(self):
        self._wmmr( 0x41, 0x2)  # move video pipeline to bypass mode
        self._wcam( self.IEXP, self._iexp )
        self._wcam( self.FEXP, self._fexp )
        self._wcam( self.PGA, 2 )
        
    #-------------------------------------------------------
#   def read(self):
#       return vframe.qpipe_get_frame(self._f, self._p)

    #-------------------------------------------------------
    def display(self, pmap):
        if gui.fqueue.qsize() < 20:
            gui.fqueue.put(pmap)
            self.display_frame_signal.emit(0)
            self._queue_limit_exceed = False
        else:
            if not self._queue_limit_exceed:
                lg.warning('video frame queue exceeds limit, seems GUI does not read from the queue')
            self._queue_limit_exceed = True

    #-------------------------------------------------------
    def processing(self):
        self.vsthread_control()
        if not iframe_event.wait(0.1):
            return

        iframe_event.clear()
        #vframe.get_inp_frame(self._f)
        if not self._vstream_on:     # prevent spurious pop from incoming queue
            return

        self._f = vframe.get_iframe()

        pbuf = self._f.pixbuf

        self.frame_signal.emit([self._f.tstamp, time.time()*1e8])

        self.fframe_histo.fill(0)
        self.window_histo.fill(0)
        window = np.copy(pbuf[240:720,320:960])
        org, top, scale = vframe.histogram(window, self.window_histo, self.org_thres, self.top_thres, self.discard)
        fframe_org, fframe_top, fframe_scale = vframe.histogram(pbuf, self.fframe_histo, 30, 30, 0)

        self._pmap = vframe.make_display_frame(pbuf)
        self.display(self._pmap)

        vframe.put_free_frame(self._f)

        self.hook.run(self)
           
    #-----------------------------------------------------------------
    def vsthread_control(self):
        if not self._vstream_on:
            if self._vstream_ena:
                vframe.start_vstream_thread()
                self._vstream_on = True
                lg.info('start low-level incoming video stream thread')
        else:
            if not self._vstream_ena:
                vframe.finish_vstream_thread();
                vsthread_finish_event.wait()
                self._vstream_on = False
                lg.info('stop low-level incoming video stream thread')

    #-----------------------------------------------------------------
    #
    #    MMR command API
    #
    #-------------------------------------------------------
    def _sock_transaction(self, fun, args):
        command_queue.put( [fun, args] )
    #-------------------------------------------------------
    def send_udp(self, data):
        return self._sock.processing(data)
        
    #-------------------------------------------------------
    def _rmmr(self, *args):
        addr    = args[0]
        data    = np.array( [0x55aa, self.READ_MMR, addr, 0], dtype=np.uint16 )
        data[3] = np.bitwise_xor.reduce(data)
        res     = self._sock.processing(data)
        cs      = np.bitwise_xor.reduce(res)
        if cs:
            lg.error('incorrect udp responce')
            
        return res[3]
        
    def rmmr(self, addr):
        self._sock_transaction(self._rmmr, [addr])
        
    #-------------------------------------------------------
    def _wmmr(self, *args):
        addr    = args[0]
        data    = args[1]
        data    = np.array( [0x55aa, self.WRITE_MMR, addr, data, 0], dtype=np.uint16 )
        data[4] = np.bitwise_xor.reduce(data)
        res     = self._sock.processing(data)
        cs      = np.bitwise_xor.reduce(res)
        if cs:
            lg.error('incorrect udp responce')
        
    def wmmr(self, addr, data):
        self._sock_transaction(self._wmmr, [addr, data])
        
    #-------------------------------------------------------
    def _wcam(self, *args):
        addr = args[0]
        data = args[1]
        cmd  = self.WR | addr
        
        self._wmmr(self.SPI_CSR,  0x1); # nCS -> 0
        self._wmmr(self.SPI_DR,   cmd); # send cmd to camera
        self._wmmr(self.SPI_DR,  data); # send value to write
        self._wmmr(self.SPI_CSR,  0x0); # nCS -> 1
        
    def wcam(self, addr, data):
        self._sock_transaction(self._wcam, [addr, data])
        
    #-------------------------------------------------------
    def _rcam(self, *args):
        addr = args[0]
        cmd  = self.RD | addr;
    
        self._wmmr(self.SPI_CSR,  0x1); # nCS -> 0
        self._wmmr(self.SPI_DR,   cmd); # send cmd to camera
        self._wmmr(self.SPI_DR,     0); # transaction to take data from camera
        self._wmmr(self.SPI_CSR,  0x0); # nCS -> 1
        return self._rmmr(self.SPI_DR);
         
    #-------------------------------------------------------
    def rcam(self, addr):
        self._sock_transaction(self._rcam, [addr])
                 
#-------------------------------------------------------------------------------
class VframeThread(threading.Thread):

    #-------------------------------------------------------
    def __init__(self, sdc, name='VFrame Thread' ):
        super().__init__()
        self.core          = sdc
        self._finish_event = threading.Event()

    #-------------------------------------------------------
    def finish(self):
        lg.info('VFrame Thread pending to finish')
        if self.core._vstream_on:
            vframe.finish_vstream_thread()
            vsthread_finish_event.wait()

        vframe.delete_frame_pool()
        self._finish_event.set()

    #-------------------------------------------------------
    def run(self):
        self.core._vstream_ena = self.core.parent.sdc_core_opt['Start/Stop Video']
        while True:
            self.core.processing()
            if self._finish_event.is_set():
                self.core.deinit()
                return

#-------------------------------------------------------------------------------

