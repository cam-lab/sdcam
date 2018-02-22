

import os
import threading
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal

import sys

from logger import logger as lg
import vframe
import gui

from udp import command_queue, TSocket
 

#-------------------------------------------------------------------------------
class TSDC_Core(QObject):

    frame_signal = pyqtSignal( int )
    
    #-------------------------------------------------------
    def __init__(self):
        super().__init__()
        
        #-----------------------------------------
        #
        #    MMR 
        #
        self.WRITE_MMR = 0x0001
        self.READ_MMR  = 0x0002
        
        self.SPI_DR    = 0x30
        self.SPI_CSR   = 0x31
        
        self.RD        = 0xA000
        self.WR        = 0xB000
        
        self.CR        = 0x0
        self.CR_S      = 0x01
        self.CR_C      = 0x02
        self.IEXP      = 0x04
        self.FEXP      = 0x06
        self.PGA       = 0x08
        self.NPULSES   = 0x0A
        self.PINCH     = 0x0C
        self.DEPTH     = 0x0E
        self.TRIM      = 0x10
        self.PWIDTH    = 0x12
        
        #-----------------------------------------
        #
        #    Video frame
        #
        self._pixmap = self.init_frame()
        self._roll_line = 1000
        self._k = 1

        vframe.init_numpy()

        self._f = vframe.TVFrame()
        self._p = vframe.TPipeRxParams()

        self._p.key = 2307
        
        vframe.qpipe_cfg(self._p)
        lg.info(os.linesep +  str(self._p))
        
        self._agc_ena = True
        
        self._kf = 0.1
        self._kp = 1.0
        self._ka = 0.2
        
        self._stim = 0
        
        self.IEXP_MIN = 0
        self.IEXP_MAX = 978
        self.FEXP_MIN = 3
        self.FEXP_MAX = 1599
        
        self._iexp = self.IEXP_MIN
        self._fexp = self.FEXP_MIN
        
        self._top_ref = 3800.0;
        
        #-----------------------------------------
        #
        #    UDP socket
        #
        self._sock = TSocket()

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
    def read(self):
        return vframe.qpipe_get_frame(self._f, self._p)

    #-------------------------------------------------------
    def display(self, pmap):
        if gui.fqueue.qsize() < 10:
            gui.fqueue.put(pmap.astype(np.uint8))
            self.frame_signal.emit(0)
        else:
            lg.warning('video frame queue exceeds limit, seems GUI does not read from the queue')

    #-------------------------------------------------------
    def processing(self):
        vframe.qpipe_get_frame(self._f, self._p)
        pbuf = self._f.pixbuf
        self.histo = np.zeros( (1024), dtype=np.uint32)
        org, top, scale = vframe.histogram(pbuf, self.histo, 30)

        kp        = self._kp
        ka        = self._ka
        iexp      = self._iexp
        fexp      = self._fexp
        IEXP_MAX  = self.IEXP_MAX
        IEXP_MIN  = self.IEXP_MIN
        FEXP_MAX  = self.FEXP_MAX
        FEXP_MIN  = self.FEXP_MIN
        stim      = self._stim
        f         = self._f
        top_ref   = self._top_ref 
        
        
        if top > 4000:
            top_ref = 0
        
        if self._agc_ena:
            s = kp*top_ref/top*(f.iexp + f.fexp/FEXP_MAX)
            stim = stim + ka*(s - stim)
            if stim < 0:
                stim = 0
                
            iexp = int(stim)
            fexp = int((stim - iexp)*FEXP_MAX)
            
            if iexp > IEXP_MAX:
                iexp = IEXP_MAX
                
            if fexp < FEXP_MIN:
                fexp = FEXP_MIN
            
            if fexp > FEXP_MAX:
                fexp = FEXP_MAX
                
            self.wcam( self.IEXP, iexp )
            self.wcam( self.FEXP, fexp )
            
            self._stim = stim
            self._iexp = iexp
            self._fexp = fexp
            
        swing = top - org
        self._k = 4096.0/swing
        vframe.scale(pbuf, org, self._k)
            
        self._pmap = np.right_shift( pbuf, 4 )
        self.display(self._pmap)
           
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
         
    def rcam(self, addr):
        self._sock_transaction(self._rcam, [addr])
                 
#-------------------------------------------------------------------------------
class TVFrameThread(threading.Thread):

    #-------------------------------------------------------
    def __init__(self, name='VFrame Thread' ):
        super().__init__()
        self._finish_event = threading.Event()
        self.core = TSDC_Core()

    #-------------------------------------------------------
    def finish(self):
        self._finish_event.set()
        lg.info('VFrame Thread pending to finish')

    #-------------------------------------------------------
    def run(self):
        self.core.init_cam()
        while True:
            self.core.processing()
            if self._finish_event.is_set():
                self.core.deinit()
                return

#-------------------------------------------------------------------------------

