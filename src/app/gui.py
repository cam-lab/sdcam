# coding: utf-8

import sys
import os
import queue
import re

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QMainWindow, QApplication, QGraphicsScene,
                             QVBoxLayout,QHBoxLayout, QSplitter, QGraphicsView, QFrame,
                             QGraphicsPixmapItem, QGraphicsItem, QDockWidget,
                             QAction)

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView



from PyQt5.Qt     import QShortcut, QKeySequence
from PyQt5.QtGui  import QIcon, QBrush, QImage, QPixmap, QColor, QKeyEvent, QFont, QResizeEvent, QTransform, QStandardItemModel
from PyQt5.QtCore import QSettings, pyqtSignal, QObject, QEvent
from PyQt5.QtCore import QT_VERSION_STR

from internal_ipkernel import InternalIPKernel

import ipycon

from logger import logger as lg

run_path, filename = os.path.split(  os.path.abspath(__file__) )
ico_path = os.path.join( run_path, 'ico' )

PROGRAM_NAME = 'Software-Defined Camera'
VERSION      = '0.1.0'

fqueue = queue.Queue()

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
    def save_settings(self):
        Settings = QSettings('cam-lab', 'pysdcam')
        Settings.setValue('main-window/geometry', self.saveGeometry() )
        Settings.setValue('main-window/state',    self.saveState());
        
    #--------------------------------------------------------------------------------    
    def restore_settings(self):
        Settings = QSettings('cam-lab', 'pysdcam')
        if Settings.contains('main-window/geometry'):
            self.restoreGeometry( Settings.value('main-window/geometry') )
            self.restoreState( Settings.value('main-window/state') )
        else:
            self.setGeometry(100, 100, 1024, 768)
        
    #--------------------------------------------------------------------------------    
    def closeEvent(self, event):
        self.save_settings()
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
    def setup_actions(self):
        self.exitAction = QAction(QIcon( os.path.join(ico_path, 'exit24.png') ), 'Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.close)

        self.ipyConsoleAction = QAction(QIcon( os.path.join(ico_path, 'ipy-console-24.png') ), 'Jupyter Console', self)
        self.ipyConsoleAction.setShortcut('Alt+S')
        self.ipyConsoleAction.setStatusTip('Launch Jupyter Console')
        self.ipyConsoleAction.triggered.connect(self.launch_jupyter_console_slot)

        self.ipyQtConsoleAction = QAction(QIcon( os.path.join(ico_path, 'ipy-qtconsole-24.png') ), 'Jupyter QtConsole', self)
        self.ipyQtConsoleAction.setShortcut('Alt+T')
        self.ipyQtConsoleAction.setStatusTip('Launch Jupyter QtConsole')
        self.ipyQtConsoleAction.triggered.connect(self.launch_jupyter_qtconsole_slot)
        
    #--------------------------------------------------------------------------------    
    def setup_menu(self):
        self.menubar = self.menuBar()
        self.controlMenu = self.menubar.addMenu('&Control')
        self.controlMenu.addAction(self.ipyConsoleAction)
        self.controlMenu.addAction(self.ipyQtConsoleAction)
        self.controlMenu.addAction(self.exitAction)
        
    #--------------------------------------------------------------------------------    
    def setup_toolbar(self):
        self.toolbar = self.addToolBar('MainToolbar')
        self.toolbar.setObjectName('main-toolbar')
        self.toolbar.addAction(self.exitAction)        
        self.toolbar.addAction(self.ipyConsoleAction)        
        self.toolbar.addAction(self.ipyQtConsoleAction)        
        
    #--------------------------------------------------------------------------------    
    def setup_main_scene(self):
        self.MainScene = QGraphicsScene(self)
        self.MainScene.setBackgroundBrush(QColor(0x20,0x20,0x20))
        self.NoVStreamPixmap = QPixmap(1280, 960)
        self.NoVStreamPixmap.fill(QColor(0x00,0x00,0x40,255))
        self.PixmapItem = self.init_pixmap_item(1280, 960, self.NoVStreamPixmap, 1)
        self.MainScene.addItem(self.PixmapItem)

        self.MainView = TGraphicsView(self.MainScene, self)
        self.MainView.setFrameStyle(QFrame.NoFrame)
    
    #--------------------------------------------------------------------------------    
    def create_log_window(self):
        self.Log = QDockWidget('Log', self, Qt.WindowCloseButtonHint)
        self.Log.setObjectName('Log Window')
        self.Log.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.Log.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.LogWidget = TLogWidget(self)
        self.Log.setWidget(self.LogWidget)
        
    #--------------------------------------------------------------------------------    
    def initUI(self, context):

        #----------------------------------------------------
        #
        #    Main Window
        #
        self.setup_actions()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_main_scene()
        self.create_log_window()

        self.addDockWidget(Qt.BottomDockWidgetArea, self.Log)
        self.setCentralWidget(self.MainView)
        
        self.set_title()
        self.restore_settings()
        
        #--------------------------------------------------------------------------------    
        self.show()
        
        self.LogWidget.update_slot('sdcam.1.log')
        
#-------------------------------------------------------------------------------
class TLogWidget(QTableWidget):
    def __init__(self, parent):
        super().__init__(0, 4, parent)
        
        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # select whole row
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)   # disable edit cells
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.horizontalHeader().resizeSection(0, 200)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setDefaultSectionSize(20)
        self.setTabKeyNavigation(False)   
        self.setAlternatingRowColors(True)  
        
    def update_slot(self, s):
        self.clear()
        with open(s, 'rb') as f:
            text = f.read().decode()
            
        l = re.split('(\d\d\d\d-\d\d-\d\d\s\d\d\:\d\d\:\d\d)\s+', text)[1:]
        loglist = list(zip(l[::2], l[1::2]))
        self.setRowCount(len(loglist))
        
        for idx, logitem in enumerate(loglist):
            tstamp = logitem[0]
            p = '(\\w+)\\s+(\\w+)\\s+\\:\\s((?:.|\n)+)'
            module, status, message = re.search(p, logitem[1]).groups()
            self.setItem(idx, 0, QTableWidgetItem(tstamp))
            self.setItem(idx, 1, QTableWidgetItem(module))
            self.setItem(idx, 2, QTableWidgetItem(status))
            self.setItem(idx, 3, QTableWidgetItem(message.strip(os.linesep)))
            
        self.scrollToBottom()
        self.setHorizontalHeaderLabels( ['Timestamp', 'Module', 'Status', 'Message'] )
            
#-------------------------------------------------------------------------------
        
