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

from udp     import command_queue, Socket, HOST_IP, DEVICE_IP, DRC_PORT
from sdc_lib import Nuc, BiasManager, Histogram, histo_bounds

import drc
 
iframe_event          = threading.Event()
vsthread_finish_event = threading.Event()

#-------------------------------------------------------------------------------
class SdcCore(QObject):

    frame_signal            = pyqtSignal( list  )
    display_frame_signal    = pyqtSignal( int )
    update_dashboard_signal = pyqtSignal( int )
    fpa_temp_signal         = pyqtSignal( float )
    forg_signal             = pyqtSignal( list )
    dac_changed_signal      = pyqtSignal( int )
    
    #-------------------------------------------------------
    def __init__(self, parent):
        super().__init__()
        
        self.parent = parent

        self.lock          = threading.Lock()
        self._set_dac_lock = threading.Lock()
        self.set_dac_lock  = threading.Lock()
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
        self.bm  = BiasManager(self)

        vframe.reg_pyobject(iframe_event,          0)
        vframe.reg_pyobject(vsthread_finish_event, 1)

        class HookStub:
            def run(self, host):
                pass

        self.hook = HookStub()

        self._init_done     = False

        self._agc_ena         = False
        self._bm_ena          = False
        self._vstream_ena     = False
        self._camera_ena      = False
        self._camvfg_ena      = False
        self._nuc_ena         = False

        self._vstream_on      = False
        self._camera_on       = False
        self._camvfg_on       = False
        self._nuc_on          = False
        
        self._fpa_toc         = 0
        self._fpa_toc_qen     = True
        self._fpa_tocr_qtime  = 0

        self.org_thres = 5
        self.top_thres = 5
        self.discard   = 0.005
        
        self._kf = 0.1
        self._kp = 0.5
        self._ka = 0.5
        
        self.rhlow  = 900
        self.rhhigh = 12000

        self.forg  = 900
        self.ftop  = 9000
        self.fgain = 1.0
        
        self.histo_cnt = 10
        
        self.rhisto = Histogram(2**14)
        self.nhisto = Histogram(2**14)
        self.fhisto = Histogram(2**10)

        self.nhisto.top = 5000
        
        #-----------------------------------------
        #
        #    Adapter Board DAC
        #
        self.dac = {
            'VREF'    : [0x19, 2300],
            'VPB'     : [0x1b, 2900],
            'VBB'     : [0x1c, 2000],
            'ADVREF'  : [0x1a, 1500]
        }

        #-----------------------------------------
        #
        #    VM1765 Parameters
        #
        self.det = {
            'GAIN' : {
                        '1.00'  : 0x7,
                        '1.125' : 0x3,
                        '1.129' : 0x5,
                        '1.50'  : 0x1,
                        '1.80'  : 0x6,
                        '2.25'  : 0x2,
                        '3.00'  : 0x4,
                        '4.50'  : 0x0
                     },
            'HFLIP' : { 'Yes' : 0, 'No' : 1 },
            'VFLIP' : { 'Yes' : 0, 'No' : 1 }
        }
        
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
    def reg_hook(self, hook):
        self.hook = hook
        hook.host = self
        
    #-------------------------------------------------------
    def init_frame(self):
        return np.tile(np.arange(4095, step=32, dtype=np.uint16), [960, 10])
    
    #-------------------------------------------------------
    def agc_slot(self, checked):
        self._agc_ena = checked
        
    #-------------------------------------------------------
    def bm_slot(self, checked):
        self._bm_ena = checked

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
        if not self._fpa_toc_qen:
            return

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
    def display(self, pmap):
        self._fqueue_size = gui.fqueue.qsize()
        if gui.fqueue.qsize() < 40:
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

        self.frame_signal.emit([self._f.tstamp, time.time()*1e8])

        if not self._camvfg_on:

            pbuf = self._f.pixbuf
            
            if self.nuc.valid:
                self.df = pbuf + 4000 - self.nuc.cframe
                self.ff = self.df.copy()

                self.rhisto.update(self._f.pixbuf)
                self.nhisto.update(self.df)
                
                self.rhlow, self.rhhigh = histo_bounds(self.rhisto.data, self.rhlow, self.rhhigh, 10)

                if self._agc_ena:
                    self.forg, self.ftop = histo_bounds(self.nhisto.data, self.forg, self.ftop, 30)
                    self.fgain = 1024/(self.ftop - self.forg + 1)


                vframe.scale(self.ff, self.forg, self.fgain)
                self.fhisto.update(self.ff)

                self._pmap = vframe.make_display_frame(self.ff)
                
                self.histo_cnt -= 1
                if self.histo_cnt == 0:
                    gui.dboard_q.put( [(self.forg,  self.fgain),  self.rhisto, self.nhisto, self.fhisto] )
                    self.update_dashboard_signal.emit(0)
                    self.forg_signal.emit([self.forg, self.fgain, pbuf.mean(), self.rhlow, self.rhhigh])

                    self.histo_cnt = 8

                self.rbuf.append(self.ff)
            else:
                self._pmap = vframe.make_display_frame(pbuf)

        else:
            pbuf = self._f.pixbuf
            self._pmap = vframe.make_display_frame(pbuf)
            
        self.display(self._pmap)

        #-------------------------------------------------------------
        #
        #    NUC
        #
        if self._nuc_on:
            self.nuc.processing()
            
        #-------------------------------------------------------------
        #
        #    Detector Bias Management
        #
        if self._bm_ena:
            self.bm.fmean_buf.append(self._f.pixbuf.mean())
            with self.bm.fmean_incoming:
                self.bm.fmean_incoming.notify()

        #-------------------------------------------------------------
        #
        #    Extension Hook
        #
        self.hook.run(self)

        vframe.put_free_frame(self._f)

        #-------------------------------------------------------------
        #
        #    FPA temperature quering
        #
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
    def _set_dac(self, addr, data):
        self._set_dac_lock.acquire()
        self.dac[addr][1] = data
        #lg.info('set dac value, {} = {}'.format(addr, self.dac[addr][1]))
        res = self._dev_fun_exec(drc.DAC_FUN, self.dac[addr][0], self.dac[addr][1])
        if not res:
            print('E: DRC -> device fun exec unsuccessful')
            
        self._set_dac_lock.release()

    #-----------------------------------------------------------------
    def set_dac(self, addr, data):
        self.set_dac_lock.acquire()
        data = int(data)
        self.dac[addr][1] = data
        self._set_dac(addr, data)
        self.dac_changed_signal.emit(0)
        self.set_dac_lock.release()

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
        self.lock.acquire()
        rid     = args[0]()
        self._drc_msg_num = (self._drc_msg_num + 1) & 0x00ff
        id      = (self._drc_msg_num & drc.ID_NUMBER_MASK) + (drc.MMR_READ << drc.ID_TYPE_OFFSET)
        data    = np.array( [id, rid], dtype=np.uint16 )
        self._drc_sock.empty()
        resp    = self._drc_sock.processing(data).astype(np.uint32)   # convert to 32-bit type due to following shift operation
        self.lock.release()
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
        self.lock.acquire()
        rid     = args[0]()
        datal   = args[1] & 0xffff
        datah   = args[1] >> 16
        self._drc_msg_num = (self._drc_msg_num + 1) & 0x00ff
        id      = (self._drc_msg_num & drc.ID_NUMBER_MASK) + (drc.MMR_WRITE << drc.ID_TYPE_OFFSET)
        data    = np.array( [id, rid, datal, datah], dtype=np.uint16 )
        self._drc_sock.empty()
        resp    = self._drc_sock.processing(data)
        self.lock.release()
        return drc.check_resp(self._drc_msg_num, resp)
        
    def wmmr(self, rid, data):
        if self._wmmr(rid, data):
            lg.info('successful MMR write')
        else:
            lg.error('MMR write failed')
        
    #-------------------------------------------------------
    def _dev_fun_exec(self, *args):
        self.lock.acquire()
        self._drc_msg_num = (self._drc_msg_num + 1) & 0x00ff
        id      = (self._drc_msg_num & drc.ID_NUMBER_MASK) + (drc.FUN_EXEC << drc.ID_TYPE_OFFSET)
        oc      = (args[0] & drc.OPCODE_MASK) + ((len(args) - 1) << drc.PCOUNT_OFFSET)
        hdr     = np.array( [id, oc], dtype=np.uint16 )
        params  = np.array( args[1:], dtype=np.uint16)
        data    = np.concatenate((hdr, params))
        self._drc_sock.empty()
        resp    = self._drc_sock.processing(data)
        res     = drc.check_resp(self._drc_msg_num, resp)
        self.lock.release()
        if res:
            return resp[1:]
        else:
            return False

#-------------------------------------------------------------------------------
class VframeThread(threading.Thread):

    #-------------------------------------------------------
    def __init__(self, sdc, name='VFrame Thread' ):
        super().__init__()
        self.core          = sdc
        self._finish_event = threading.Event()
        self.core.bm.start()

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
        self.core._nuc_ena     = self.core.parent.sdc_core_opt['NUC On/Off']
        self.core._bm_ena      = self.core.parent.sdc_core_opt['Bias Manager On/Off']
        
        while True:
            try:
                self.core.processing()
            except Exception as e:
                lg.info(str(e))

            if self._finish_event.is_set():
                lg.info('BM Thread pending to finish')
                self.core.bm.finish()
                self.core.bm.join()
                lg.info('BM Thread finished')
                self.core.deinit()
                return

#-------------------------------------------------------------------------------

