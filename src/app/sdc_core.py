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

import matplotlib.pyplot as plt
import collections

from PyQt5.QtCore import QObject, pyqtSignal

import sys

from logger import logger as lg
import vframe
import gui

from udp import command_queue, Socket, HOST_IP, DEVICE_IP, DRC_PORT

import drc
 
iframe_event          = threading.Event()
vsthread_finish_event = threading.Event()

#-------------------------------------------------------------------------------
class Nuc:
    def __init__(self, host):
        self.host      = host
        self.prep_rqst = False
        self.fcnt      = 0
        self.fpool     = []
        self.cframe    = None
        self.valid     = False
        
        self.apply     = False
        
        self.shtr_begin_line = 10
        
        self.afcount   = 2

    def launch(self):
        self.fcnt       = 0;
        self.fpool      = []
        self.prep_rqst  = True

        self.host._wmmr(drc.cam.cr_c, 7 << 16)
        if self.host._wmmr(drc.cam.cr_s, (self.afcount + 1) << 16):
            lg.info('successful set shuttered frame count to {}'.format(self.afcount))
        else:
            lg.warning('set shuttered frame count failed')

        return self.host._wmmr(drc.cam.shtr, self.shtr_begin_line)  # return status for check MMR write acknoledge

    def processing(self):
        if self.prep_rqst:
            self.prep_cf()

    def prep_cf(self):
        f = self.host._f.copy()

        self.fpool.append(f)
        if f.shtr_on():
                
            self.fcnt += 1
            if self.fcnt == 2:
                self.cframe = self.host._f.pixbuf.copy()
                lg.info('{} blinded frame'.format(self.fcnt))
            elif self.fcnt > 2 and self.fcnt <= self.afcount + 1:
                self.cframe += self.host._f.pixbuf
                lg.info('{} blinded frame'.format(self.fcnt))
                if self.fcnt == self.afcount + 1:
                    self.cframe = (self.cframe/self.afcount).astype(np.uint16)
                    lg.info('cframe complete')
                    self.valid  = True

        elif self.fcnt:
            if not f.shtr_on():
                self.prep_rqst = False
                s = ' '.join([str(int(f.shtr_on())) for f in self.fpool])
                lg.info('NUC complete, frames {}, {}'.format(len(self.fpool), s))
                
                shtr_end_line = self.host._rmmr(drc.cam.shtr)
                shtr_begin_line = self.shtr_begin_line
                
                lg.info('bl: {}, el: {}, bl_new: {}'.format(shtr_begin_line, shtr_end_line, self.shtr_begin_line))

#-------------------------------------------------------------------------------
class Histogram:

    def __init__(self, size):
        self.data    = np.zeros(size, dtype=np.uint32)
        self.max     = 0
        self.org     = 0
        self.top     = size-1
        self.k       = 0.1

    def update(self, f):
        self.data.fill(0)
        vframe.histo(f, self.data, 1)
        self.max += self.k*(self.data[:-1].max() - self.max)

#-------------------------------------------------------------------------------
class SdcCore(QObject):

    frame_signal            = pyqtSignal( list  )
    display_frame_signal    = pyqtSignal( int )
    update_dashboard_signal = pyqtSignal( int )
    fpa_temp_signal         = pyqtSignal( float )
    
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

        self._f  = vframe.Vframe()
        self.nuc = Nuc(self)

        vframe.reg_pyobject(iframe_event,          0)
        vframe.reg_pyobject(vsthread_finish_event, 1)

        class HookStub:
            def run(self, host):
                pass

        self.hook = HookStub()

        self._init_done     = False

        self._agc_ena         = False
        self._vstream_ena     = False
        self._camera_ena      = False
        self._camvfg_ena      = False
        self._nuc_ena         = False

        self._vstream_on      = False
        self._camera_on       = False
        self._camvfg_on       = False
        self._nuc_on          = False
        
        self._fpa_toc         = 0
        self._fpa_tocr_qtime  = 0

        self.org_thres = 5
        self.top_thres = 5
        self.discard   = 0.005
        
        self._kf = 0.1
        self._kp = 0.5
        self._ka = 0.5
        
        self.forg  = 900
        self.ftop  = 9000
        self.fgain = 1.0
        
        self.histo_cnt = 10
        
        self.rhisto = Histogram(2**14)
        self.nhisto = Histogram(2**14)
        self.fhisto = Histogram(2**10)

        self.nhisto.top = 2000
        #-----------------------------------------
        #
        #    Adapter Board DAC
        #

        self.dac = {
            'VREF'         : [0x19, 2300],
            'VPB'          : [0x1b, 2900],
            'VBB'          : [0x1c, 2000],
            'ADC_DRV_VREF' : [0x1a, 1500]
        }

#       self.VREF         = 0x19
#       self.VPB          = 0x1b
#       self.VBB          = 0x1c
#       self.ADC_DRV_VREF = 0x1a
#
#       self.vref         = 2300
#       self.vpb          = 2900
#       self.vbb          = 2000
#       self.adc_drv_vref = 1500

        
        #-----------------------------------------
        #
        #    UDP socket
        #
        self._drc_sock    = Socket(HOST_IP, DRC_PORT, DEVICE_IP)
        self._drc_msg_num = 0
        

        self.fig, self.ax = plt.subplots()
        #plt.show()
        
        self.rbuf = collections.deque(maxlen=16)

    #-------------------------------------------------------
    def deinit(self):
        self._drc_sock.close()
    
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
    def nuc_ena_slot(self, checked):
        self._nuc_ena = checked

    #-------------------------------------------------------
    def fpa_tocr_query(self):
        t = time.time();
        if t - self._fpa_tocr_qtime >= 4:
            resp = int(self._rmmr(drc.cam.dba_tocr))
            if resp:
                self._fpa_toc = resp
                T = round( (resp - 8192)*0.01330525 + 36.039396, 3 )
                #lg.info('toc: {}, T: {}°C'.format(resp, T))
                self.fpa_temp_signal.emit(T)
            else:
                lg.error('device not respond while cam.dba.tocr query')

            self._fpa_tocr_qtime = t

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
    def average_frame(self, n=16):
        if n > 16:
            lg.warning('invalid frame count {}, max count: 16'.format(n))
            return None

        pool = self.rbuf[0].copy().astype(np.uint32)

        for i in range(n-1):
            pool += self.rbuf[i+1]

        p = (pool/n).astype(np.uint16)
        
        return p

    #-------------------------------------------------------
    def fbounds(self, f, org, top, thld):
        b = np.where(f >= thld)[0][:-1]
        
        if not b.size:
            return org, top

        min = b.min()
        max = b.max()
        
        k = 0.1

        org += k*(min - org)
        top += k*(max - top)
        
        return int(org), int(top)

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

        self.frame_signal.emit([self._f.tstamp, time.time()*1e8])

        if not self._camvfg_on:

            pbuf = self._f.pixbuf
            
            if self.nuc.valid:
                self.df = pbuf + 2000 - self.nuc.cframe
                self.ff = self.df.copy()

                self.rhisto.update(self._f.pixbuf)
                self.nhisto.update(self.df)

                if self._agc_ena:
                    self.forg, self.ftop = self.fbounds(self.nhisto.data, self.forg, self.ftop, 30)
                    self.fgain = 1024/(self.ftop - self.forg + 1)


                vframe.scale(self.ff, self.forg, self.fgain)
                self.fhisto.update(self.ff)

                self._pmap = vframe.make_display_frame(self.ff)
                
                self.histo_cnt -= 1
                if self.histo_cnt == 0:
                    gui.dboard_q.put( [(self.forg,  self.fgain),  self.rhisto, self.nhisto, self.fhisto] )
                    self.update_dashboard_signal.emit(0)
                    self.histo_cnt = 8
                    
            else:
                self._pmap = vframe.make_display_frame(pbuf)

        else:
            pbuf = self._f.pixbuf
            self._pmap = vframe.make_display_frame(pbuf)
            
        self.display(self._pmap)

        if self._nuc_on:
            self.nuc.processing()

        self.rbuf.append(pbuf)
        self.hook.run(self)

        vframe.put_free_frame(self._f)

        self.fpa_tocr_query()

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
                    
        if not self._nuc_on:
            if self._nuc_ena:
                lg.info('try to turn on NUC')
                if self.nuc.launch():
                    self._nuc_on = True
                    lg.info('NUC turned on')
        else:
            if not self._nuc_ena:
                lg.info('turn off NUC')
                self._nuc_on = False

        if not self._init_done:
            self._init_done = True

    #-----------------------------------------------------------------
    def set_dac(self, addr, data):
        self.dac[addr][1] = data
        res = self._dev_fun_exec(drc.DAC_FUN, self.dac[addr][0], self.dac[addr][1])
        if res:
            print(res)
        else:
            print('E: DRC -> device fun exec unsuccessful')

    #-----------------------------------------------------------------
    #
    #    MMR command API
    #
    #-------------------------------------------------------
    def _sock_transaction(self, fun, args):
        command_queue.put( [fun, args] )
    #-------------------------------------------------------
    def send_udp(self, data):
        return self._drc_sock.processing(data)
        
    #-------------------------------------------------------
    def _rmmr(self, *args):
        rid     = args[0]()
        self._drc_msg_num = (self._drc_msg_num + 1) & 0x00ff
        id      = (self._drc_msg_num & drc.ID_NUMBER_MASK) + (drc.MMR_READ << drc.ID_TYPE_OFFSET)
        data    = np.array( [id, rid], dtype=np.uint16 )
        self._drc_sock.empty()
        resp    = self._drc_sock.processing(data).astype(np.uint32)   # convert to 32-bit type due to following shift operation
        if drc.check_resp(self._drc_msg_num, resp):
            return resp[1] + (resp[2] << 16)
        else:
            return None
        
    def rmmr(self, rid):
        res = self._rmmr(rid)
        if res != None:
            return res, hex(res)
        else:
            lg.error('MMR read failed')
        
    #-------------------------------------------------------
    def _wmmr(self, *args):
        rid     = args[0]()
        datal   = args[1] & 0xffff
        datah   = args[1] >> 16
        self._drc_msg_num = (self._drc_msg_num + 1) & 0x00ff
        id      = (self._drc_msg_num & drc.ID_NUMBER_MASK) + (drc.MMR_WRITE << drc.ID_TYPE_OFFSET)
        data    = np.array( [id, rid, datal, datah], dtype=np.uint16 )
        self._drc_sock.empty()

        resp    = self._drc_sock.processing(data)
        return drc.check_resp(self._drc_msg_num, resp)
        
    def wmmr(self, rid, data):
        if self._wmmr(rid, data):
            lg.info('successful MMR write')
        else:
            lg.error('MMR write failed')
        
    #-------------------------------------------------------
    def _dev_fun_exec(self, *args):
        self._drc_msg_num = (self._drc_msg_num + 1) & 0x00ff
        id      = (self._drc_msg_num & drc.ID_NUMBER_MASK) + (drc.FUN_EXEC << drc.ID_TYPE_OFFSET)
        oc      = (args[0] & drc.OPCODE_MASK) + ((len(args) - 1) << drc.PCOUNT_OFFSET)
        hdr     = np.array( [id, oc], dtype=np.uint16 )
        params  = np.array( args[1:], dtype=np.uint16)
        data    = np.concatenate((hdr, params))
        self._drc_sock.empty()
        resp    = self._drc_sock.processing(data)
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
        self.core._agc_ena     = self.core.parent.sdc_core_opt['Automatic Gain Control']
        self.core._camera_ena  = self.core.parent.sdc_core_opt['Start/Stop Camera']
        self.core._camvfg_ena  = self.core.parent.sdc_core_opt['Start/Stop CamVFG']
        while True:
            self.core.processing()
            if self._finish_event.is_set():
                self.core.deinit()
                return

#-------------------------------------------------------------------------------

