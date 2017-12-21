#!/usr/bin/env python3
# coding: utf-8

import sys
import os
import re

import threading
import time

import numpy as np

run_path, filename = os.path.split(  os.path.abspath(__file__) )
resources_path = run_path
sys.path.append( resources_path )

sys.path.append('bin/release')

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore    import QObject, pyqtSignal
from PyQt5.QtCore    import QT_VERSION_STR, pyqtSignal

import vframe
import gui

#-------------------------------------------------------------------------------
class TVFrame(QObject):
    
    frame_signal = pyqtSignal( np.ndarray )
    
    def __init__(self):
        super().__init__()
        self._pixmap = self.init_frame()
        self._roll_line = 1000
        
        vframe.init_numpy()
    
        self._f = vframe.TVFrame()
        self._p = vframe.TPipeRxParams()

        self._p.key = 2307

        vframe.qpipe_cfg(self._p)
        print(self._p)
        
            
    def init_frame(self):
        return np.tile(np.arange(4095, step=32, dtype=np.uint16), [960, 10])
    
    def generate(self):
        self._pmap = np.right_shift( self._pixmap, 4 ).astype(dtype=np.uint8)
        self._pmap[:, self._roll_line] = 255
        if self._roll_line < 1280-1:
            self._roll_line += 1
        else:
            self._roll_line = 0
        
        return self._pmap
    
    def read(self):
        vframe.qpipe_get_frame(self._f, self._p)
            
        self._pmap = np.right_shift( self._f.pixbuf, 4 ).astype(dtype=np.uint8)

        return self._pmap
        
    
    def display(self):
        self.frame_signal.emit(self.read())
    
#-------------------------------------------------------------------------------
class TVFrameThread(threading.Thread):
    
    def __init__(self, name='VFrame Thread' ):
        super().__init__()
        self._finish_event = threading.Event()
        self.frame = TVFrame()
        
    def finish(self):
        self._finish_event.set()
        print('VFrame Thread pending to finish')
        
    def run(self):
        while True:
            self.frame.display()
        #    time.sleep(0.04)
            if self._finish_event.is_set():
                return
        
            
#-------------------------------------------------------------------------------
class TSDCam:

    def __init__(self):
        self.mwin = gui.MainWindow()
        
        self.vfthread = TVFrameThread()
        self.vfthread.start()
        
        self.mwin.close_signal.connect(self.finish)
        self.vfthread.frame.frame_signal.connect(self.mwin.show_frame_slot)
        
        
    def finish(self):
        print('self::finish')
        self.vfthread.finish()
        self.vfthread.join()
        
        
    def generate_frame(self):
        self.frame
        
    
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    print('Qt Version: ' + QT_VERSION_STR)

    app  = QApplication(sys.argv)

    with open( os.path.join(resources_path, 'sdcam.qss'), 'rb') as fqss:
        qss = fqss.read().decode()
        qss = re.sub(os.linesep, '', qss )
    app.setStyleSheet(qss)

    sdcam = TSDCam()

    sys.exit( app.exec_() )
#-------------------------------------------------------------------------------



