#!/usr/bin/env python3
#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: Root program file
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
from PyQt5.QtCore    import QSettings, QT_VERSION_STR, pyqtSignal
from PyQt5.QtGui     import QIcon

from internal_ipkernel import InternalIPKernel

from sdc_core import *
import gui
import ipycon
import settings

from logger   import logger as lg
from logger   import LOG_FILE
from logger   import setup_logger
from udp      import SocketThread
from monitor  import AppMonitorThread

import drc

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
class Sdcam(QObject, InternalIPKernel):

    def __init__(self, app, args):
        
        super().__init__()
        
        self.default_sdc_core_opt = { 'Start/Stop Video'       : False,
                                      'Automatic Gain Control' : False,
                                      'Start/Stop Camera'      : False,
                                      'Start/Stop CamVFG'      : False }

        self.restore_settings()
        
        sdc = SdcCore(self)
        self.init_ipkernel('qt5', { 'sdcam' : self,
                                    'sdc'   : sdc,
                                    'drc'   : drc })

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
        self.amthread = AppMonitorThread(os.path.abspath(LOG_FILE))
        self.vfthread = VframeThread(sdc)
        self.usthread = SocketThread()
        
        #-------------------------------------------------------------
        #
        #    Signal/Slot connections
        #
        self.amthread.monitor.file_changed_signal.connect(self.mwin.log_widget.update_slot,
                                                          Qt.QueuedConnection)
        
        if args.console:
            ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file.replace('\\', '/'),
                                          self.settings,
                                          args.console)

        app.aboutToQuit.connect(self.finish)

        self.mwin.agcAction.trig_signal.connect(self.vfthread.core.agc_slot, Qt.QueuedConnection)
        self.mwin.vstreamAction.trig_signal.connect(self.vfthread.core.vstream_slot, Qt.QueuedConnection)
        self.mwin.cameraEnableAction.trig_signal.connect(self.vfthread.core.camera_ena_slot, Qt.QueuedConnection)
        self.mwin.camvfgEnableAction.trig_signal.connect(self.vfthread.core.camvfg_ena_slot, Qt.QueuedConnection)

        self.vfthread.core.display_frame_signal.connect(self.mwin.show_frame_slot, Qt.QueuedConnection)
        self.vfthread.core.frame_signal.connect(self.amthread.monitor.frame_slot, Qt.QueuedConnection)
        
        self.amthread.monitor.update_data_signal.connect(self.mwin.telemetry_widget.update_slot, Qt.QueuedConnection)
        self.mwin.rstatAction.triggered.connect(self.amthread.monitor.reset_statistics, Qt.QueuedConnection)

        self.mwin.close_signal.connect(self.finish)
        self.mwin.close_signal.connect(app.quit)

        #-------------------------------------------------------------
        #
        #    Threads start
        #
        self.amthread.start()
        lg.info('start application monitoring thread')

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
        self.amthread.finish()
        self.amthread.join()

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
        ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file, self.settings, 'shell')

    #---------------------------------------------------------------------------
    def launch_jupyter_qtconsole_slot(self):
        ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file, self.settings, 'qt')

    #---------------------------------------------------------------------------
    def restore_settings(self):
        Settings = QSettings('camlab', 'sdcam')
        if Settings.contains('Application/Settings'):
            self.settings = settings.read('Application/Settings')
        else:
            lg.warning('application settings not exist, use default')
            self.settings = settings.app_settings
            
        if Settings.contains('sdc_core/options'):
            self.sdc_core_opt = Settings.value('sdc_core/options')
        else:
            lg.warning('sdc core options not exist, use default')
            self.sdc_core_opt = self.default_sdc_core_opt

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
    app.setWindowIcon(QIcon(os.path.join(resources_path, 'ico', 'camlab.jpeg')))

    sdcam = Sdcam(app, args)
    
    # Very important, IPython-specific step: this gets GUI event loop
    # integration going, and it replaces calling app.exec()
    #sdcam.mwin.ipkernel.start()
    sdcam.ipkernel.start()
    #sys.exit( app.exec() )

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
    
#-------------------------------------------------------------------------------


