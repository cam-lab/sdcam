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

#-------------------------------------------------------------------------------
class TGraphicsView(QGraphicsView):
    
    def __init__(self, scene, parent):
        super().__init__(scene)
        self.parent = parent
        
    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        
        
#-------------------------------------------------------------------------------
class MainWindow(QMainWindow):

    PROGRAM_NAME = 'Software-Defined Camera'

    #--------------------------------------------------------------------------------    
    def __init__(self):
        super().__init__()

        self.initUI()

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
        
        #--------------------------------------------------------------------------------    

        self.show()
        
#-------------------------------------------------------------------------------

