# coding: utf-8

import sys
import os
import queue
import re

from math import sqrt

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QMainWindow, QApplication, QGraphicsScene,
                             QVBoxLayout,QHBoxLayout, QSplitter, QGraphicsView, 
                             QFrame, QGraphicsPixmapItem, QGraphicsItem, 
                             QDockWidget, QAction)

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QAbstractItemView, 
                             QHeaderView)
from PyQt5.QtGui     import QIcon, QImage, QPixmap, QColor, QTransform
from PyQt5.QtCore    import QSettings, pyqtSignal, QObject, QEvent
from PyQt5.QtCore    import QT_VERSION_STR

from internal_ipkernel import InternalIPKernel

import ipycon

from logger import logger as lg

from badpix import TBadPix

run_path, filename = os.path.split(  os.path.abspath(__file__) )
ico_path = os.path.join( run_path, 'ico' )

PROGRAM_NAME = 'Software-Defined Camera'
VERSION      = '0.1.0'

fqueue = queue.Queue()

#-------------------------------------------------------------------------------
class TGraphicsView(QGraphicsView):
    
    #---------------------------------------------------------------------------
    def __init__(self, scene, parent):
        super().__init__(scene)
        self.parent = parent
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        
    #---------------------------------------------------------------------------
    def wheelEvent(self, event):
        steps = 1 if event.angleDelta().y() > 0 else -1
        factor = 1 + 0.25*steps
        
        oldPos = self.mapToScene(event.pos())
        hsbar = self.horizontalScrollBar().value()
        vsbar = self.verticalScrollBar().value()
        if (factor > 1 and  hsbar < 128000 and vsbar < 128000) or \
           (factor < 1 and (hsbar > 0      or  vsbar > 0)):
            self.scale(factor, factor)
            newPos = self.mapToScene(event.pos())
            delta  = newPos - oldPos
            self.translate(delta.x(), delta.y())
            
            visible_rect   = self.mapToScene(self.viewport().geometry()).boundingRect()
            visible_widht  = int(visible_rect.width())
            visible_height = int(visible_rect.height())
            
            ratio_x = self.viewport().width()/visible_rect.width()
            ratio_y = self.viewport().width()/visible_rect.height()
            
            self.parent.set_zoom(ratio_x)
            
    #---------------------------------------------------------------------------
    def mousePressEvent(self, event):
        
        if event.button() == Qt.RightButton:
            view_x = event.pos().x()
            view_y = event.pos().y()
            scene_pos = self.mapToScene(event.pos())
            scene_x = int(scene_pos.x())
            scene_y = int(scene_pos.y())
            #lg.info('pos: ' + str(view_x) + ', ' + str(view_y) + '| scene: ' + str(scene_x) + ', ' + str(scene_y))
            
            self.parent.bad_pix.toggle_pixel( (scene_x, scene_y) )

        QGraphicsView.mousePressEvent(self, event)
       
    #---------------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        view_x = event.pos().x()
        view_y = event.pos().y()
        scene_pos = self.mapToScene(event.pos())
        scene_x = int(scene_pos.x())
        scene_y = int(scene_pos.y())
        self.parent.set_cursor_pos(view_x, view_y, scene_x, scene_y)
        QGraphicsView.mouseMoveEvent(self, event)
                
#-------------------------------------------------------------------------------
class MainWindow(QMainWindow, InternalIPKernel):

    close_signal = pyqtSignal()
    
    #---------------------------------------------------------------------------
    def __init__(self, app, context):
        super().__init__()

        self.app = app
        self.init_ipkernel('qt', context)

        self.initUI(context)

        self.zoom         = 1.0
        self.view_cpos_x  = 0
        self.view_cpos_y  = 0
        self.scene_cpos_x = 0
        self.scene_cpos_y = 0
        
        self.bad_pix = TBadPix()
        
    #---------------------------------------------------------------------------
    def set_title(self, text = ''):
        text = ' - ' + text if len(text) > 0 else ''
        self.setWindowTitle(PROGRAM_NAME + ' v' + VERSION + text)
        
    #---------------------------------------------------------------------------
    def save_settings(self):
        Settings = QSettings('cam-lab', 'pysdcam')
        Settings.setValue('main-window/geometry', self.saveGeometry() )
        Settings.setValue('main-window/state',    self.saveState());
        
    #---------------------------------------------------------------------------
    def restore_settings(self):
        Settings = QSettings('cam-lab', 'pysdcam')
        if Settings.contains('main-window/geometry'):
            self.restoreGeometry( Settings.value('main-window/geometry') )
            self.restoreState( Settings.value('main-window/state') )
        else:
            self.setGeometry(100, 100, 1024, 768)
        
    #---------------------------------------------------------------------------
    def closeEvent(self, event):
        self.save_settings()
        self.close_signal.emit()
        QWidget.closeEvent(self, event)
        lg.info('Main Window closed')

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

    #---------------------------------------------------------------------------
    def init_pixmap_item(self, width, heigh, pixmap, zval):
        pixmap_item = QGraphicsPixmapItem(pixmap)
        pixmap_item.setZValue(zval)
        pixmap_item.setCacheMode(QGraphicsItem.NoCache)
        
        return pixmap_item

    #--------------------------------------------------------------------------------    
    def show_frame_slot(self, frame):
        if fqueue.empty():
            return 

        img_data = fqueue.get()
        img = QImage(img_data,
                     img_data.shape[1], 
                     img_data.shape[0], 
                     QImage.Format_RGB888)

        for pix in self.bad_pix.pixels():
            img.setPixelColor(pix[0], pix[1], QColor(0, 255, 0))
        
        self.show_image(img)
        
    #---------------------------------------------------------------------------
    def show_image(self, img):
        pmap = QPixmap.fromImage(img)
        self.PixmapItem.setPixmap(pmap)
    
    #---------------------------------------------------------------------------
    def launch_jupyter_console_slot(self):
        ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file, 'shell')
        
    #---------------------------------------------------------------------------
    def launch_jupyter_qtconsole_slot(self):
        ipycon.launch_jupyter_console(self.ipkernel.abs_connection_file, 'qt')

    #---------------------------------------------------------------------------
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
        
        self.agcAction = QAction(QIcon( os.path.join(ico_path, 'agc-24.png') ), 'Automatic Gain Control', self)
        self.agcAction.setShortcut('Alt+G')
        self.agcAction.setStatusTip('Automatic Gain Control')
        self.agcAction.setCheckable(True)
        self.agcAction.setChecked(True)
                
    #---------------------------------------------------------------------------
    def setup_menu(self):
        self.menubar = self.menuBar()
        self.controlMenu = self.menubar.addMenu('&Control')
        self.controlMenu.addAction(self.ipyConsoleAction)
        self.controlMenu.addAction(self.ipyQtConsoleAction)
        self.controlMenu.addAction(self.agcAction)
        self.controlMenu.addAction(self.exitAction)
        
    #---------------------------------------------------------------------------
    def setup_toolbar(self):
        self.toolbar = self.addToolBar('MainToolbar')
        self.toolbar.setObjectName('main-toolbar')
        self.toolbar.addAction(self.exitAction)        
        self.toolbar.addAction(self.ipyConsoleAction)        
        self.toolbar.addAction(self.ipyQtConsoleAction)        
        self.toolbar.addAction(self.agcAction)        
        
    #---------------------------------------------------------------------------
    def setup_main_scene(self):
        self.MainScene = QGraphicsScene(self)
        self.MainScene.setBackgroundBrush(QColor(0x20,0x20,0x20))
        self.NoVStreamPixmap = QPixmap(1280, 960)
        self.NoVStreamPixmap.fill(QColor(0x00,0x00,0x40,255))
        self.PixmapItem = self.init_pixmap_item(1280, 960, self.NoVStreamPixmap, 1)
        self.MainScene.addItem(self.PixmapItem)

        self.MainView = TGraphicsView(self.MainScene, self)
        self.MainView.setFrameStyle(QFrame.NoFrame)
    
    #---------------------------------------------------------------------------
    def create_log_window(self):
        self.Log = QDockWidget('Log', self, Qt.WindowCloseButtonHint)
        self.Log.setObjectName('Log Window')
        self.Log.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.Log.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.LogWidget = TLogWidget(self)
        self.Log.setWidget(self.LogWidget)
        
    #---------------------------------------------------------------------------
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
        
        self.statusBar().showMessage('Ready')
        
        #-----------------------------------------------------------------------
        self.show()
        
    #---------------------------------------------------------------------------
    def update_status_bar(self):
        text = 'Zoom: {:.1f} | View: {:d} {:d} | Scene: {:d} {:d}'.format(self.zoom, 
                                                                          self.view_cpos_x,  self.view_cpos_y,
                                                                          self.scene_cpos_x, self.scene_cpos_y)
        self.statusBar().showMessage(text)
        
    #---------------------------------------------------------------------------
    def set_zoom(self, zoom):
        self.zoom = zoom
        self.update_status_bar()
        
    #---------------------------------------------------------------------------
    def set_cursor_pos(self, vx, vy, sx, sy):
        self.view_cpos_x  = vx
        self.view_cpos_y  = vy
        self.scene_cpos_x = sx
        self.scene_cpos_y = sy
        self.update_status_bar()
                
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
        self.setHorizontalHeaderLabels( ['Timestamp', 'Module', 'Status', 'Message'] )
        
        self.StatusDictColor = { 'INFO'    : '#00FF00',
                                 'DEBUG'   : '#00FFFF',
                                 'WARNING' : '#FFFF00',
                                 'ERROR'   : '#FF0000' }

    def update_slot(self, s):
        with open(s, 'rb') as f:
            text = f.read().decode()
            
        l = re.split('(\d\d\d\d-\d\d-\d\d\s\d\d\:\d\d\:\d\d)\s+', text)[1:]
        loglist = list(zip(l[::2], l[1::2]))
        ll_len  = len(loglist)
        count   = ll_len if ll_len < 30 else 30
        self.setRowCount(count)

        for idx, logitem in enumerate(loglist[ll_len-count:]):
            tstamp = logitem[0]
            p = '(\\w+)\\s+(\\w+)\\s+\\:\\s((?:.|\n)+)'
            module, status, message = re.search(p, logitem[1]).groups()
            
            tstamp_item  = QTableWidgetItem(tstamp)
            module_item  = QTableWidgetItem(module)
            status_item  = QTableWidgetItem(status)
            message_item = QTableWidgetItem(message.strip(os.linesep))

            tstamp_item.setForeground(QColor('#F0F0F0'))
            module_item.setForeground(QColor('#E3B449'))
            status_item.setForeground(QColor(self.StatusDictColor[status]))
            message_item.setForeground(QColor('#D0D0D0'))
            
            tstamp_item.setTextAlignment(Qt.AlignTop)
            module_item.setTextAlignment(Qt.AlignTop)
            status_item.setTextAlignment(Qt.AlignTop)
            message_item.setTextAlignment(Qt.AlignTop)
            
            self.setItem(idx, 0, tstamp_item )
            self.setItem(idx, 1, module_item )
            self.setItem(idx, 2, status_item )
            self.setItem(idx, 3, message_item)
            
        self.scrollToBottom()
            
#-------------------------------------------------------------------------------
        
