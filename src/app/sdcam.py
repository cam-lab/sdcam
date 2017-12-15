#!/usr/bin/env python3
# coding: utf-8

import sys
import os
import re

run_path, filename = os.path.split(  os.path.abspath(__file__) )
resources_path = run_path
sys.path.append( resources_path )

sys.path.append('bin/release')

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore    import QT_VERSION_STR

import gui

#-------------------------------------------------------------------------------
class TSDCam:

    def __init__(self):
        self.mwin = gui.MainWindow()
        
        
    
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



