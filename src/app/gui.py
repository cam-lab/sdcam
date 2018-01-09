# coding: utf-8

import sys
import os
import queue

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QMainWindow, QApplication, QGraphicsScene,
                             QVBoxLayout,QHBoxLayout, QSplitter, QGraphicsView, QFrame,
                             QGraphicsPixmapItem, QGraphicsItem, QDockWidget,
                             QAction)


from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QImage, QPixmap, QColor, QKeyEvent, QFont, QResizeEvent
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent
from PyQt5.QtCore import QT_VERSION_STR

# Import the console machinery from ipython
from qtconsole.rich_ipython_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager

from internal_ipkernel import InternalIPKernel


PROGRAM_NAME = 'Software-Defined Camera'
VERSION      = '0.1.0'

fqueue = queue.Queue()

#-------------------------------------------------------------------------------
class TIPythonWidget(RichJupyterWidget):
    """ Convenience class for a live IPython console widget. 
        We can replace the standard banner using the customBanner argument"""
    def __init__(self,customBanner=None,*args,**kwargs):
        super(TIPythonWidget, self).__init__(*args,**kwargs)
        if customBanner!=None: self.banner=customBanner
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel_manager.kernel.gui = 'qt'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            get_app_qt5().exit()            
        self.exit_requested.connect(stop)

    def pushVariables(self,variableDict):
        """ Given a dictionary containing name:value pairs, 
            push those variables to the IPython console widget """
        self.kernel_manager.kernel.shell.push(variableDict)
    def clearTerminal(self):
        """ Clears the terminal """
        self._control.clear()    
    def printText(self,text):
        """ Prints some plain text to the console """
        self._append_plain_text(text)        
    def executeCommand(self,command):
        """ Execute a command in the frame of the console widget """
        self._execute(command,False)
#-------------------------------------------------------------------------------
class TGraphicsView(QGraphicsView):
    
    def __init__(self, scene, parent):
        super().__init__(scene)
        self.parent = parent
        
    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        
#-------------------------------------------------------------------------------
class MainWindow(QMainWindow, InternalIPKernel):

    close_signal = pyqtSignal()
    
    #--------------------------------------------------------------------------------    
    def __init__(self, app, context):
        super().__init__()

        self.app = app
        self.init_ipkernel('qt', context)

        self.initUI(context)

        self.app.lastWindowClosed.connect(self.app.quit)
        self.app.aboutToQuit.connect(self.cleanup_consoles)
        
    #--------------------------------------------------------------------------------    
    def set_title(self, text = ''):
        text = ' - ' + text if len(text) > 0 else ''
        self.setWindowTitle(PROGRAM_NAME + ' v' + VERSION + text)
        
    #--------------------------------------------------------------------------------    
    def closeEvent(self, event):
        Settings = QSettings('cam-lab', 'pysdcam')
        Settings.setValue('main-window/geometry', self.saveGeometry() )
        Settings.setValue('main-window/state',    self.saveState());
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
        pmap= fqueue.get()
        img_data = pmap 
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
    def initUI(self, context):

        #----------------------------------------------------
        #
        #    Main Window
        #
        
        #self.ipy = QDockWidget('IPy', self, Qt.WindowCloseButtonHint)
        #self.ipy.setObjectName('IPython QtConsole')
        #self.ipy.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        #self.ipy.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        #ipy = TIPythonWidget(customBanner='Embedded IPython console')
        #ipy.pushVariables({'sdcam':context})
        #self.ipy.setWidget(ipy)
        
        self.MainScene = QGraphicsScene(self)
        self.MainScene.setBackgroundBrush(QColor(0x20,0x20,0x20))
        self.NoVStreamPixmap = QPixmap(1280, 960)
        self.NoVStreamPixmap.fill(QColor(0x00,0x00,0x40,255))
        self.PixmapItem = self.init_pixmap_item(1280, 960, self.NoVStreamPixmap, 1)
        self.MainScene.addItem(self.PixmapItem)
        
        self.MainView = TGraphicsView(self.MainScene, self)
        self.MainView.setFrameStyle(QFrame.NoFrame)

    #    self.addDockWidget(Qt.RightDockWidgetArea, self.ipy)
        self.setCentralWidget(self.MainView)
        
        self.set_title()
        
        Settings = QSettings('cam-lab', 'pysdcam')
        if Settings.contains('main-window/geometry'):
            self.restoreGeometry( Settings.value('main-window/geometry') )
            self.restoreState( Settings.value('main-window/state') )
        else:
            self.setGeometry(100, 100, 1024, 768)
        
        #--------------------------------------------------------------------------------    

        self.show()
        
#-------------------------------------------------------------------------------

