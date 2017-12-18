#!/usr/bin/env python3
# coding: utf-8

import sys
import os
import re

import threading
import time

run_path, filename = os.path.split(  os.path.abspath(__file__) )
resources_path = run_path
sys.path.append( resources_path )

sys.path.append('bin/release')

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore    import QT_VERSION_STR

import gui

#-------------------------------------------------------------------------------
class TVFrameThread(threading.Thread):
    def __init__(self, name='VFrame Thread' ):
        super().__init__()
        self._finish_event = threading.Event()
        
    def finish(self):
        self._finish_event.set()
        print('VFrame Thread pending to finish')
        
    def run(self):
        while True:
            print('slon')
            time.sleep(0.5)
            if self._finish_event.is_set():
                return
        
#-------------------------------------------------------------------------------
class TSDCam:

    def __init__(self):
        self.mwin = gui.MainWindow()
        
        self.vfthread = TVFrameThread()
        self.vfthread.start()
        
        self.mwin.close_signal.connect(self.finish)
        
        
    def finish(self):
        print('self::finish')
        self.vfthread.finish()
        self.vfthread.join()
    
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



