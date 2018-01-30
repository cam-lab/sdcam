

import os
import threading
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal

from logger import logger as lg
import vframe
import gui

from udp import command_queue

WRITE_MMR = 0x0001
READ_MMR  = 0x0002
DELAY     = 0x0003

#-------------------------------------------------------------------------------
class TVFrame(QObject):

    frame_signal = pyqtSignal( int )
    
    def __init__(self):
        super().__init__()
        self._pixmap = self.init_frame()
        self._roll_line = 1000
        self._k = 1

        vframe.init_numpy()

        self._f = vframe.TVFrame()
        self._p = vframe.TPipeRxParams()

        self._p.key = 2307

        vframe.qpipe_cfg(self._p)
        lg.info(os.linesep +  str(self._p))


    def init_frame(self):
        return np.tile(np.arange(4095, step=32, dtype=np.uint16), [960, 10])

    def generate(self):
        time.sleep(0.04)
        self._pmap = np.right_shift( self._pixmap, 4 ).astype(dtype=np.uint8)
        self._pmap[:, self._roll_line] = 255
        if self._roll_line < 1280-1:
            self._roll_line += 1
        else:
            self._roll_line = 0

        return self._pmap

    def read(self):
        return vframe.qpipe_get_frame(self._f, self._p)

    def display(self, pmap):
        if gui.fqueue.qsize() < 10:
            gui.fqueue.put(pmap.astype(np.uint8))
            self.frame_signal.emit(0)
        else:
            lg.warning('video frame queue exceeds limit, seems GUI does not read from the queue')

    def processing(self):
        vframe.qpipe_get_frame(self._f, self._p)
        self._pmap = np.right_shift( self._f.pixbuf, 4 )
        self._pmap = self._pmap*self._k
        self.display(self._pmap)
           
    def send_udp(self, data):
        item = [data, self]
        command_queue.put(item)
        
    def rmmr(self, addr):
        data = np.array( [0x55aa, READ_MMR, addr, 0], dtype=np.uint16 )
        data[3] = np.bitwise_xor.reduce(data)
        self.send_udp(data)
    
    def wmmr(self, addr, data):
        data = np.array( [0x55aa, WRITE_MMR, addr, data, 0], dtype=np.uint16 )
        data[4] = np.bitwise_xor.reduce(data)
        self.send_udp(data)
         
#-------------------------------------------------------------------------------
class TVFrameThread(threading.Thread):

    def __init__(self, name='VFrame Thread' ):
        super().__init__()
        self._finish_event = threading.Event()
        self.frame = TVFrame()

    def finish(self):
        self._finish_event.set()
        lg.info('VFrame Thread pending to finish')

    def run(self):
        while True:
            self.frame.processing()
            if self._finish_event.is_set():
                return

#-------------------------------------------------------------------------------

