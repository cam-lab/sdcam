# coding: utf-8

import sys
import os

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QMainWindow, QApplication, QGraphicsScene,
                             QVBoxLayout,QHBoxLayout, QSplitter, QGraphicsView, QFrame,
                             QAction)


from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QColor, QKeyEvent, QFont, QResizeEvent
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent
from PyQt5.QtCore import QT_VERSION_STR

PROGRAM_NAME = 'Software-Defined Camera'
VERSION      = '0.1.0'


#-------------------------------------------------------------------------------
class TGraphicsView(QGraphicsView):
    
    def __init__(self, scene, parent):
        super().__init__(scene)
        self.parent = parent
        
    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        
        
#-------------------------------------------------------------------------------
class MainWindow(QMainWindow):

    #--------------------------------------------------------------------------------    
    def __init__(self):
        super().__init__()

        self.initUI()
        
    #--------------------------------------------------------------------------------    
    def set_title(self, text = ''):
        text = ' - ' + text if len(text) > 0 else ''
        self.setWindowTitle(PROGRAM_NAME + ' v' + VERSION + text)
        
    #--------------------------------------------------------------------------------    
    def closeEvent(self, event):
        Settings = QSettings('cam-lab', 'pysdcam')
        Settings.setValue( 'geometry', self.saveGeometry() )
        QWidget.closeEvent(self, event)

    #--------------------------------------------------------------------------------    
    def initUI(self):

        #----------------------------------------------------
        #
        #    Main Window
        #
        self.MainScene = QGraphicsScene(self)
        self.MainScene.setBackgroundBrush(QColor(0x20,0x20,0x20))
        self.MainView = TGraphicsView(self.MainScene, self)
        self.MainView.setFrameStyle(QFrame.NoFrame)
        self.setCentralWidget(self.MainView)
        
        self.set_title()
        
        Settings = QSettings('cam-lab', 'pysdcam')
        if Settings.contains('geometry'):
            self.restoreGeometry( Settings.value('geometry') )
        else:
            self.setGeometry(100, 100, 1024, 768)

        
        #--------------------------------------------------------------------------------    

        self.show()
        
#-------------------------------------------------------------------------------

