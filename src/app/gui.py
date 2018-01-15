# coding: utf-8

import sys
import os
import queue

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QMainWindow, QApplication, QGraphicsScene,
                             QVBoxLayout,QHBoxLayout, QSplitter, QGraphicsView, QFrame,
                             QGraphicsPixmapItem, QGraphicsItem, QDockWidget,
                             QAction, QPlainTextEdit)


from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QImage, QPixmap, QColor, QKeyEvent, QFont, QResizeEvent, QTransform
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent
from PyQt5.QtCore import QT_VERSION_STR

# Import the console machinery from ipython
from qtconsole.rich_ipython_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager

from internal_ipkernel import InternalIPKernel

import ipycon

run_path, filename = os.path.split(  os.path.abspath(__file__) )
ico_path = os.path.join( run_path, 'ico' )

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
        newSize   = event.size();
        dX        = 20;
        dY        = 20;
        viewScale = 1.0;
        width     = 1280;
        height    = 960;
        
        if (newSize.width() > (width + dX)) and (newSize.height() > ( + dY)):
            scaleX = (self.contentsRect().width()  - dX)/float(width);
            scaleY = (self.contentsRect().height() - dY)/float(height);
            viewScale = min(scaleX,scaleY);
        
        self.setTransform(QTransform.fromScale(viewScale,viewScale), False);
        
        QGraphicsView.resizeEvent(self, event)
        
#-------------------------------------------------------------------------------
class MainWindow(QMainWindow, InternalIPKernel):

    close_signal = pyqtSignal()
    
    #--------------------------------------------------------------------------------    
    def __init__(self, app, context):
        super().__init__()

        self.app = app
        self.init_ipkernel('qt', context)
        #self.ipkernel.connection_file

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
    def launch_jupyter_console_slot(self):
        ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file, 'shell')
        
    #--------------------------------------------------------------------------------    
    def launch_jupyter_qtconsole_slot(self):
        ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file, 'qt')

    #--------------------------------------------------------------------------------    
    def initUI(self, context):

        #----------------------------------------------------
        #
        #    Main Window
        #
        exitAction = QAction(QIcon( os.path.join(ico_path, 'exit24.png') ), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)
        
        ipyConsoleAction = QAction(QIcon( os.path.join(ico_path, 'ipy-console-24.png') ), 'Jupyter Console', self)
        ipyConsoleAction.setShortcut('Alt+S')
        ipyConsoleAction.setStatusTip('Launch Jupyter Console')
        ipyConsoleAction.triggered.connect(self.launch_jupyter_console_slot)
        
        ipyQtConsoleAction = QAction(QIcon( os.path.join(ico_path, 'ipy-qtconsole-24.png') ), 'Jupyter QtConsole', self)
        ipyQtConsoleAction.setShortcut('Alt+T')
        ipyQtConsoleAction.setStatusTip('Launch Jupyter QtConsole')
        ipyQtConsoleAction.triggered.connect(self.launch_jupyter_qtconsole_slot)

        #--------------------------------------------
        #
        #    Main Menu
        #
        menubar = self.menuBar()
        controlMenu = menubar.addMenu('&Control')
        controlMenu.addAction(ipyConsoleAction)
        controlMenu.addAction(ipyQtConsoleAction)
        controlMenu.addAction(exitAction)
        
        #--------------------------------------------
        #
        #    Toolbar
        #
        toolbar = self.addToolBar('MainToolbar')
        toolbar.setObjectName('main-toolbar')
        toolbar.addAction(exitAction)        
        toolbar.addAction(ipyConsoleAction)        
        toolbar.addAction(ipyQtConsoleAction)        
        
        
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
    
        self.Log = QDockWidget('Log', self, Qt.WindowCloseButtonHint)
        self.Log.setObjectName('Log Window')
        self.Log.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.Log.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.LogWidget = QPlainTextEdit(self)
        self.Log.setWidget(self.LogWidget)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.Log)
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

