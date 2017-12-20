# coding: utf-8

import sys
import os

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QMainWindow, QApplication, QGraphicsScene,
                             QVBoxLayout,QHBoxLayout, QSplitter, QGraphicsView, QFrame,
                             QGraphicsPixmapItem, QGraphicsItem,
                             QAction)


from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QImage, QPixmap, QColor, QKeyEvent, QFont, QResizeEvent
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent
from PyQt5.QtCore import QT_VERSION_STR

import cv2

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

    close_signal = pyqtSignal()
    
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
        self.close_signal.emit()
        QWidget.closeEvent(self, event)

    #--------------------------------------------------------------------------------    
    def init_pixmap_item(self, width, heigh, pixmap, zval):
        pixmap_item = QGraphicsPixmapItem(pixmap)
        pixmap_item.setZValue(zval)
        pixmap_item.setCacheMode(QGraphicsItem.NoCache)
        
        return pixmap_item
        
    #--------------------------------------------------------------------------------    
    def show_frame_slot(self, frame):
        img_data = frame  # cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        img = QImage(img_data, 
                     img_data.shape[1], 
                     img_data.shape[0], 
                     QImage.Format_Grayscale8)

        self.show_image(img)
        
    #--------------------------------------------------------------------------------    
    def show_image(self, img):
        pmap = QPixmap.fromImage(img)
        self.PixmapItem.setPixmap(pmap)
    
    #--------------------------------------------------------------------------------    
    def initUI(self):

        #----------------------------------------------------
        #
        #    Main Window
        #
        self.MainScene = QGraphicsScene(self)
        self.MainScene.setBackgroundBrush(QColor(0x20,0x20,0x20))
        self.NoVStreamPixmap = QPixmap(1280, 960)
        self.NoVStreamPixmap.fill(QColor(0x00,0x00,0x40,255))
        self.PixmapItem = self.init_pixmap_item(1280, 960, self.NoVStreamPixmap, 1)
        self.MainScene.addItem(self.PixmapItem)
        
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

