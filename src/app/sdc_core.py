

import os
import threading
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal

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
        self.WRITE_MMR = 0x0001
        self.READ_MMR  = 0x0002
        self.DELAY     = 0x0003
        
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
        
        self._pixmap = self.init_frame()
        self._roll_line = 1000
        self._k = 1

        vframe.init_numpy()

        self._f = vframe.TVFrame()
        self._p = vframe.TPipeRxParams()

        self._p.key = 2307

        vframe.qpipe_cfg(self._p)
        lg.info(os.linesep +  str(self._p))
        
        self._sock = TSocket()

    #-------------------------------------------------------
    def deinit(self):
        self._sock.shutdown()
        self._sock.close()
    
    #-------------------------------------------------------
    def init_frame(self):
        return np.tile(np.arange(4095, step=32, dtype=np.uint16), [960, 10])

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
        self._pmap = np.right_shift( self._f.pixbuf, 4 )
        self._pmap = self._pmap*self._k
        self.display(self._pmap)
           
    #-------------------------------------------------------
    def _sock_transaction(self, fun, args):
        command_queue.put( [fun, args] )
    #-------------------------------------------------------
    def send_udp(self, data):
        return self._sock.processing(data)
        
    #-------------------------------------------------------
    def _rmmr(self, *args):
        addr = args[0]
        data = np.array( [0x55aa, self.READ_MMR, addr, 0], dtype=np.uint16 )
        data[3] = np.bitwise_xor.reduce(data)
        res = self._sock.processing(data)
        cs  = np.bitwise_xor.reduce(res)
        if cs:
            lg.error('incorrect udp responce')
            
        return res[3]
        
    def rmmr(self, addr):
        self._sock_transaction(self._rmmr, [addr])
        
    #-------------------------------------------------------
    def _wmmr(self, *args):
        addr = args[0]
        data = args[1]
        data = np.array( [0x55aa, self.WRITE_MMR, addr, data, 0], dtype=np.uint16 )
        data[4] = np.bitwise_xor.reduce(data)
        res = self._sock.processing(data)
        cs  = np.bitwise_xor.reduce(res)
        if cs:
            lg.error('incorrect udp responce')
        
    def wmmr(self, addr, data):
        self._sock_transaction(self._wmmr, [addr, data])
        
    #-------------------------------------------------------
    def _wcam(self, *args):
        addr = args[0]
        data = args[1]
        cmd = self.WR | addr
        
        self._wmmr(self.SPI_CSR,  0x1); # nCS -> 0
        self._wmmr(self.SPI_DR,   cmd); # send cmd to camera
        self._wmmr(self.SPI_DR,  data); # send value to write
        self._wmmr(self.SPI_CSR,  0x0); # nCS -> 1
        
    def wcam(self, addr, data):
        self._sock_transaction(self._wcam, [addr, data])
        
    #-------------------------------------------------------
    def _rcam(self, *args):
        addr = args[0]
        cmd = self.RD | addr;
    
        self._wmmr(self.SPI_CSR,  0x1); # nCS -> 0
        self._wmmr(self.SPI_DR,   cmd); # send cmd to camera
        self._wmmr(self.SPI_DR,     0); # transaction to take data from camera
        self._wmmr(self.SPI_CSR,  0x0); # nCS -> 1
        self._rmmr(self.SPI_DR);
         
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
        while True:
            self.core.processing()
            if self._finish_event.is_set():
                self.core.deinit()
                return

#-------------------------------------------------------------------------------

