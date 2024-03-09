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

sys.path.append( os.path.abspath(os.path.join('bin', 'release')))

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore    import QObject, pyqtSignal, QFileSystemWatcher
from PyQt5.QtCore    import QT_VERSION_STR, pyqtSignal

#from IPython.utils.frame import extract_module_locals
#from ipykernel.kernelapp import IPKernelApp
from internal_ipkernel   import InternalIPKernel

from sdc_core import *
import gui
import ipycon
from logger   import logger as lg
from logger   import LOG_FILE
from logger   import setup_logger
from udp      import TSocketThread
from watcher  import TWatcherThread

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
class TSDCam(QObject, InternalIPKernel):

    def __init__(self, app, args):
        
        super().__init__()

        sdc = TSDC_Core()
        self.init_ipkernel('qt5', { 'sdcam' : self, 'sdc' : sdc })

        #-------------------------------------------------------------
        #
        #    Main window
        #
        self.mwin = gui.MainWindow(app, self)
        lg.info('start main window')

        #-------------------------------------------------------------
        #
        #    Thread objects
        #
        self.wdthread = TWatcherThread(os.path.abspath(LOG_FILE))
        self.vfthread = TVFrameThread(sdc)
        self.usthread = TSocketThread()
        
        #-------------------------------------------------------------
        #
        #    Signal/Slot connections
        #
        self.wdthread.watcher.file_changed_signal.connect(self.mwin.LogWidget.update_slot,
                                                          Qt.QueuedConnection)
        
        if args.console:
            ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file.replace('\\', '/'),
                                          args.console)

        app.aboutToQuit.connect(self.finish)

        self.mwin.agcAction.triggered.connect(self.vfthread.core.agc_slot, Qt.QueuedConnection)
        self.vfthread.core.frame_signal.connect(self.mwin.show_frame_slot, Qt.QueuedConnection)

        self.mwin.close_signal.connect(self.finish)
        self.mwin.close_signal.connect(app.quit)
        

        #-------------------------------------------------------------
        #
        #    Threads start
        #
        self.wdthread.start()
        lg.info('start watcher thread')

        self.vfthread.start()
        lg.info('start video frame thread')

        self.usthread.start()
        lg.info('start udp socket thread')

    #-----------------------------------------------------------------
    def finish(self):
        lg.info('sdcam finishing...')
        self.usthread.finish()
        self.usthread.join()
        self.vfthread.finish()
        self.vfthread.join()
        self.wdthread.finish()
        self.wdthread.join()

        #-------------------------------------------------------------
        #
        #    Exit Jupyter Kernel Application event loop
        #
        import jupyter_client

        cfname = self.ipkernel.connection_file
        cfile  = jupyter_client.find_connection_file(cfname)
        client = jupyter_client.AsyncKernelClient(connection_file=cfile)
        client.load_connection_file()
        client.start_channels()
        client.shutdown()

        lg.info('sdcam has finished')

    def generate_frame(self):
        self.frame
    
    #---------------------------------------------------------------------------
    def launch_jupyter_console_slot(self):
        ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file, 'shell')

    #---------------------------------------------------------------------------
    def launch_jupyter_qtconsole_slot(self):
        ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file, 'qt')

#-------------------------------------------------------------------------------
def main():
    print('Qt Version: ' + QT_VERSION_STR)
    QApplication.setDesktopSettingsAware(False)

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--console',
                        const='shell',
                        nargs='?',
                        help='launch jupyter console on program start')

    parser.add_argument('-l', '--log-level', 
                        default='info',
                        help='specify log level: debug, info, warning, error, defult: info')

    args = parser.parse_args()
    setup_logger(args.log_level)

    app  = get_app_qt5(sys.argv)
    
    with open( os.path.join(resources_path, 'sdcam.qss'), 'rb') as fqss:
        qss = fqss.read().decode()
        qss = re.sub(os.linesep, ' ', qss )
    app.setStyleSheet(qss)

    sdcam = TSDCam(app, args)
    
    # Very important, IPython-specific step: this gets GUI event loop
    # integration going, and it replaces calling app.exec()
    #sdcam.mwin.ipkernel.start()
    sdcam.ipkernel.start()
    #sys.exit( app.exec() )

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
    
#-------------------------------------------------------------------------------


