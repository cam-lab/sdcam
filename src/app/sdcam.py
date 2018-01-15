#!/usr/bin/env python3
# coding: utf-8

import sys
import os
import re

import threading
import time
import subprocess
import shlex
import argparse

import numpy as np

run_path, filename = os.path.split(  os.path.abspath(__file__) )
resources_path = run_path
sys.path.append( resources_path )

sys.path.append('bin/release')

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore    import QObject, pyqtSignal
from PyQt5.QtCore    import QT_VERSION_STR, pyqtSignal


from IPython.utils.frame import extract_module_locals
from ipykernel.kernelapp import IPKernelApp

import vframe
import gui

#-------------------------------------------------------------------------------
class TLogger(QObject):
    log_signal = pyqtSignal( str )

    def __init__(self):
        super().__init__()

    def info(self, s):
        self.log_signal.emit(s)

#-------------------------------------------------------------------------------

Logger = TLogger()

#-------------------------------------------------------------------------------
def get_app_qt5(*args, **kwargs):
    """Create a new qt5 app or return an existing one."""
    app = QApplication.instance()
    if app is None:
        if not args:
            args = ([''],)
        app = QApplication(*args, **kwargs)
    return app

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
        print(self._p)
        
            
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
        vframe.qpipe_get_frame(self._f, self._p)
        self._pmap = np.right_shift( self._f.pixbuf, 4 ).astype(dtype=np.uint8)
        self._pmap = self._pmap*self._k
        return self._pmap
        
    
    def display(self):
        pmap = self.read()
        #pmap = self.generate()
        gui.fqueue.put(pmap)
        self.frame_signal.emit(0)
    
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
            if self._finish_event.is_set():
                return
            
#-------------------------------------------------------------------------------
class TConsoleLaunchThread(threading.Thread):

    
    def __init__(self, connection_file, console, name='Jupyter Console Launch Thread' ):
        super().__init__()
        self.connection_file = connection_file
        self.console = console
        
        #self.logger = TLogger()
        
    def run(self):

        Logger.info('waiting for start Jupyter kernel...')
        
        while True:
            if os.path.exists(self.connection_file):
                break
            time.sleep(0.3)
        
        if self.console == 'shell':
            console = 'jupyter console --existing ' + self.connection_file
            cmd = 'terminator -T "IPython Console" --new-tab -e "' + console + '"'
        elif self.console == 'qt':
            cmd = 'jupyter qtconsole --style=monokai --existing ' + self.connection_file
        else:
            Logger.info('E: invalid console type: ' + self.console)
            return
        
        Logger.info('launching Jupyter console...')
        Logger.info(cmd)
             
        p = subprocess.Popen( shlex.split(cmd), universal_newlines = True,
                     stdin  = subprocess.PIPE,
                     stdout = subprocess.PIPE,
                     stderr = subprocess.PIPE )
        
        Logger.info('Jupyter Console has launched')

#-------------------------------------------------------------------------------
def create_jupyter_console(cfile, ctype):
    clthread = TConsoleLaunchThread(cfile, ctype)
    clthread.start()
    
#-------------------------------------------------------------------------------
class TSDCam:

    def __init__(self, app, args):
        self.mwin = gui.MainWindow(app, { 'sdcam' : self })
        
        Logger.log_signal.connect(self.mwin.LogWidget.appendPlainText,
                                  Qt.QueuedConnection)
                
        self.vfthread = TVFrameThread()
        self.vfthread.start()
                
        if args.console:
            create_jupyter_console(self.mwin.ipkernel.abs_connection_file, args.console)
                
        self.mwin.close_signal.connect(self.finish)
        self.vfthread.frame.frame_signal.connect(self.mwin.show_frame_slot,
                                                 Qt.QueuedConnection)
        
    def finish(self):
        print('self::finish')
        self.vfthread.finish()
        self.vfthread.join()

    def generate_frame(self):
        self.frame
        
    
#-------------------------------------------------------------------------------
def main():
    print('Qt Version: ' + QT_VERSION_STR)

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--console', 
                        const='shell',
                        nargs='?',
                        help='launch jupyter console on program start')
    
    args = parser.parse_args()
#   print(args)
#   sys.exit(0)
    
    #app  = QApplication(sys.argv)
    app = get_app_qt5(sys.argv)

    with open( os.path.join(resources_path, 'sdcam.qss'), 'rb') as fqss:
        qss = fqss.read().decode()
        qss = re.sub(os.linesep, '', qss )
    app.setStyleSheet(qss)

    sdcam = TSDCam(app, args)

    #sys.exit( app.exec_() )
    sdcam.mwin.ipkernel.start()

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
    
#-------------------------------------------------------------------------------


