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

import drc
 
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

        self._agc_ena         = False
        self._vstream_ena     = False
        self._camera_ena      = False
        self._camvfg_ena         = False

        self._vstream_on      = False
        self._camera_on       = False
        self._camvfg_on          = False
        
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
        self._drc_msg_num = 0

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
    def camera_ena_slot(self, checked):
        self._camera_ena = checked

    #-------------------------------------------------------
    def camvfg_ena_slot(self, checked):
        self._camvfg_ena = checked

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

        if not self._camera_on:
            if self._camera_ena:
                lg.info('try to turn on camera')
                if self._wmmr(drc.cam.cr_s, drc.CAMERA_ENA_MASK):
                    self._camera_on = True
                    lg.info('camera successfully turned on')
        else:
            if not self._camera_ena:
                lg.info('try to turn off camera')
                if self._wmmr(drc.cam.cr_c, drc.CAMERA_ENA_MASK):
                    self._camera_on = False
                    lg.info('camera successfully turned off')
                
        if not self._camvfg_on:
            if self._camvfg_ena:
                lg.info('try to turn on camera VFG')
                if self._wmmr(drc.cam.cr_s, drc.VFG_ENA_MASK):
                    self._camvfg_on = True
                    lg.info('video test generator successfully turned on')
        else:
            if not self._camvfg_ena:
                lg.info('try to turn off camera VFG')
                if self._wmmr(drc.cam.cr_c, drc.VFG_ENA_MASK):
                    self._camvfg_on = False
                    lg.info('video test generator successfully turned off')

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
        rid     = args[0]()
        self._drc_msg_num += 1
        id      = (self._drc_msg_num & drc.ID_NUMBER_MASK) + (drc.MMR_READ << drc.ID_TYPE_OFFSET)
        data    = np.array( [id, rid], dtype=np.uint16 )
        self._sock.empty()
        resp    = self._sock.processing(data)
        if drc.check_resp(self._drc_msg_num, resp):
            return resp[1] + (resp[2] << 16)
        else:
            return None
        
    def rmmr(self, rid):
        res = self._rmmr(rid)
        if res != None:
            return res
        else:
            print('MMR read failed')
        
    #-------------------------------------------------------
    def _wmmr(self, *args):
        rid     = args[0]()
        datal   = args[1]
        datah   = args[1] >> 16
        self._drc_msg_num += 1
        id      = (self._drc_msg_num & drc.ID_NUMBER_MASK) + (drc.MMR_WRITE << drc.ID_TYPE_OFFSET)
        data    = np.array( [id, rid, datal, datah], dtype=np.uint16 )
        self._sock.empty()
        resp    = self._sock.processing(data)
        return drc.check_resp(self._drc_msg_num, resp)
        
    def wmmr(self, rid, data):
        if self._wmmr(rid, data):
            print('successful MMR write')
        else:
            print('MMR write failed')
        
    #-------------------------------------------------------
    def _dev_fun_exec(self, *args):
        self._drc_msg_num += 1
        id      = (self._drc_msg_num & drc.ID_NUMBER_MASK) + (drc.FUN_EXEC << drc.ID_TYPE_OFFSET)
        oc      = (args[0] & drc.OPCODE_MASK) + ((len(args) - 1) << drc.PCOUNT_OFFSET)
        hdr     = np.array( [id, oc], dtype=np.uint16 )
        params  = np.array( args[1:], dtype=np.uint16)
        data    = np.concatenate((hdr, params))
        resp    = self._sock.processing(data)
        res     = drc.check_resp(self._drc_msg_num, resp)
        if res:
            return resp[1:]
        else:
            return False

#   def _wcam(self, *args):
#       addr = args[0]
#       data = args[1]
#       cmd  = self.WR | addr
#
#       self._wmmr(self.SPI_CSR,  0x1); # nCS -> 0
#       self._wmmr(self.SPI_DR,   cmd); # send cmd to camera
#       self._wmmr(self.SPI_DR,  data); # send value to write
#       self._wmmr(self.SPI_CSR,  0x0); # nCS -> 1
#
#   def wcam(self, addr, data):
#       self._sock_transaction(self._wcam, [addr, data])
        
    #-------------------------------------------------------
#   def _rcam(self, *args):
#       addr = args[0]
#       cmd  = self.RD | addr;
#
#       self._wmmr(self.SPI_CSR,  0x1); # nCS -> 0
#       self._wmmr(self.SPI_DR,   cmd); # send cmd to camera
#       self._wmmr(self.SPI_DR,     0); # transaction to take data from camera
#       self._wmmr(self.SPI_CSR,  0x0); # nCS -> 1
#       return self._rmmr(self.SPI_DR);
         
    #-------------------------------------------------------
#   def rcam(self, addr):
#       self._sock_transaction(self._rcam, [addr])
                 
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
        self.core._camera_ena  = self.core.parent.sdc_core_opt['Start/Stop Camera']
        self.core._camvfg_ena  = self.core.parent.sdc_core_opt['Start/Stop CamVFG']
        while True:
            self.core.processing()
            if self._finish_event.is_set():
                self.core.deinit()
                return

#-------------------------------------------------------------------------------

