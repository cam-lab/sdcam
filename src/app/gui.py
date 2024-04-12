#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: GUI stuff
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
import queue
import re

from math import sqrt

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QMainWindow, QApplication, QGraphicsScene,
                             QVBoxLayout, QHBoxLayout, QSplitter, QGraphicsView,
                             QFrame, QGraphicsPixmapItem, QGraphicsItem, 
                             QDockWidget, QAction)

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QAbstractItemView, 
                             QHeaderView, QRubberBand)
from PyQt5.QtGui     import QCursor, QIcon, QImage, QPixmap, QColor, QTransform
from PyQt5.QtCore    import QSettings, pyqtSignal, QObject, QEvent, QRect, QRectF, QPoint, QPointF, QSize
from PyQt5.QtCore    import QT_VERSION_STR

import settings

from logger   import logger as lg
from badpix   import BadPix

from vframe   import FRAME_SIZE_X, FRAME_SIZE_Y, OUT_PIX_W

run_path, filename = os.path.split(  os.path.abspath(__file__) )
ico_path = os.path.join( run_path, 'ico' )

PROGRAM_NAME = 'Software-Defined Camera'
VERSION      = '0.2.0'

fqueue = queue.Queue()

#-------------------------------------------------------------------------------
def cursor_within_scene(pos):
    if pos.x() >= 0 and pos.x() < FRAME_SIZE_X and pos.y() >= 0 and pos.y() < FRAME_SIZE_Y:
        return True
    else:
        return False

#-------------------------------------------------------------------------------
class GraphicsView(QGraphicsView):
    
    #  zoom by rect selection
    rectChanged = pyqtSignal(QRect)
    
    #---------------------------------------------------------------------------
    def __init__(self, scene, parent):
        super().__init__(scene)
        self.scene  = scene
        self.parent = parent
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        #  zoom by rect selection
        self.rubberBand       = QRubberBand(QRubberBand.Rectangle, self)
        self.origin           = QPoint()
        self.changeRubberBand = False
        self.setMouseTracking(True)
        
    #---------------------------------------------------------------------------
    def process_cursor_pos(self, pos):
        vx   = pos.x()
        vy   = pos.y()
        spos = self.mapToScene(pos)
        sx   = int(spos.x())
        sy   = int(spos.y())
        
        cursor_on_scene = cursor_within_scene(spos)
        if cursor_on_scene:
            pval = self.parent.img.pixelColor(sx, sy).rgba64().blue() >> (16 - OUT_PIX_W)
        else:
            pval = None

        self.parent.update_cursor_pos(vx, vy, sx, sy, pval)
        
        return cursor_on_scene

    #---------------------------------------------------------------------------
    def calc_zoom_factor(self):
        visible_rect  = self.mapToScene(self.viewport().geometry()).boundingRect()
        ratio_x       = self.viewport().width()/visible_rect.width()

        self.parent.update_zoom(ratio_x)

    #---------------------------------------------------------------------------
    def fit_scene_to_view(self):
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self.calc_zoom_factor()
        self.process_cursor_pos(self.cursor().pos() - self.parent.geometry().topLeft() - self.pos() )

    #---------------------------------------------------------------------------
    #
    #    Event handlers
    #
    def wheelEvent(self, event):
        #lg.info('pos: ' + str(self.cursor().pos().x()) + ', ' + str(self.cursor().pos().y()))
        #vx, vy, sx, sy, pval = self.process_cursor_pos(self.cursor().pos())

        modifiers = QApplication.keyboardModifiers()
        coef      = 0.5 if modifiers == Qt.ShiftModifier else 0.1
        steps     = 1 if event.angleDelta().y() > 0 else -1
        factor    = 1 + steps*coef
        self.scale(factor, factor)
        self.calc_zoom_factor()
        
        self.process_cursor_pos(event.pos())
            
    #---------------------------------------------------------------------------
    def mousePressEvent(self, event):
        
        cursor_on_scene = self.process_cursor_pos(event.pos())

        #-------------------------------------------------------------
        #
        #   Left Mouse Button click
        #
        modifiers = QApplication.keyboardModifiers()
        if event.button() == Qt.LeftButton:
            if modifiers == Qt.ShiftModifier and cursor_on_scene:
                self.origin = event.pos()
                self.rubberBand.setGeometry(QRect(self.origin, QSize()))
                self.rectChanged.emit(self.rubberBand.geometry())
                self.rubberBand.show()
                self.changeRubberBand = True
            else:
                self.setDragMode(QGraphicsView.ScrollHandDrag)

        #-------------------------------------------------------------
        #
        #   Right Mouse Button click
        #
        if event.button() == Qt.RightButton:
            spos = self.mapToScene(event.pos())
            sx   = int(spos.x())
            sy   = int(spos.y())
            self.parent.bad_pix.toggle_pixel( (sx, sy) )

        QGraphicsView.mousePressEvent(self, event)
       
    #---------------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        cursor_on_scene = self.process_cursor_pos(event.pos())

        #  for rect selection
        if event.buttons() == Qt.LeftButton:
            if self.changeRubberBand and cursor_on_scene:

                self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
                self.rectChanged.emit(self.rubberBand.geometry())
                return


        QGraphicsView.mouseMoveEvent(self, event)
        
    #---------------------------------------------------------------------------
    def mouseReleaseEvent(self, event):
        if self.changeRubberBand:
            self.changeRubberBand = False
            self.rubberBand.hide()
            self.zoom_area = self.mapToScene(self.rubberBand.geometry()).boundingRect()
            self.fitInView(self.zoom_area, Qt.KeepAspectRatio)
            self.calc_zoom_factor()

        self.process_cursor_pos(event.pos())
        self.setDragMode(QGraphicsView.NoDrag)
        QGraphicsView.mouseReleaseEvent(self, event)
                
#-------------------------------------------------------------------------------
class GraphicsScene(QGraphicsScene):

    def __init__(self, parent):
        super().__init__(parent)

#-------------------------------------------------------------------------------
#
#     Main window
#
class MainWindow(QMainWindow):

    close_signal = pyqtSignal()
    
    #---------------------------------------------------------------------------
    def __init__(self, app, parent):

        super().__init__()

        self.app   = app
        self.parent = parent

        self.initUI()

        self.zoom         = 1.0
        self.view_cpos_x  = 0
        self.view_cpos_y  = 0
        self.scene_cpos_x = 0
        self.scene_cpos_y = 0
        
        scene_org = self.main_view.pos() + self.main_view.mapFromScene(0, 0)
        QCursor().setPos( self.geometry().topLeft() + scene_org)
        
        self.bad_pix = BadPix()
        
        
    #---------------------------------------------------------------------------
    def set_title(self, text = ''):
        text = ' - ' + text if len(text) > 0 else ''
        self.setWindowTitle(PROGRAM_NAME + ' v' + VERSION + text)
        
    #---------------------------------------------------------------------------
    def save_settings(self):
        Settings = QSettings('camlab', 'sdcam')
        Settings.setValue('main-window/geometry', self.saveGeometry() )
        Settings.setValue('main-window/state',    self.saveState())
        Settings.setValue('sdc_core/options',     self.parent.sdc_core_opt)

    #---------------------------------------------------------------------------
    def restore_main_window(self):
        Settings = QSettings('camlab', 'sdcam')
        if Settings.contains('main-window/geometry'):
            self.restoreGeometry( Settings.value('main-window/geometry') )
            self.restoreState( Settings.value('main-window/state') )
            
        else:
            lg.warning('main window settings not exist, use default')
            self.setGeometry(100, 100, 1024, 768)

    #---------------------------------------------------------------------------
    def closeEvent(self, event):
        self.save_settings()
        self.close_signal.emit()
        QWidget.closeEvent(self, event)
        lg.info('Main Window closed')

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
                     QImage.Format_RGB30)


        self.img = img
        for pix in self.bad_pix.pixels():
            if cursor_within_scene(QPointF(pix[0], pix[1])):
               img.setPixelColor(pix[0], pix[1], QColor(0, 255, 0))
        
        self.show_image(img)
        
    #---------------------------------------------------------------------------
    def show_image(self, img):
        pmap = QPixmap.fromImage(img)
        self.pixmap_item.setPixmap(pmap)
    
    #---------------------------------------------------------------------------
    class CheckedAction(QAction):

        trig_signal = pyqtSignal( bool )

        def __init__(self, icon_off, icon_on, text, parent  ):
            self.icon_on  = QIcon( os.path.join(ico_path, icon_on) )
            self.icon_off = QIcon( os.path.join(ico_path, icon_off) )

            super().__init__(self.icon_off, text, parent)
            self.triggered.connect(self.trigAction)
            
            self.setStatusTip(text)
            self.setCheckable(True)
            self.setChecked(parent.parent.sdc_core_opt[text])

        def updateIcon(self):
            self.setIcon(self.icon_on) if self.isChecked() else self.setIcon(self.icon_off)
            
        def trigAction(self):
            self.updateIcon()
            self.parent().parent.sdc_core_opt[self.text()] = self.isChecked()
            self.trig_signal.emit(self.isChecked())
            
    def setup_actions(self):
        #-------------------------------------------------------------
        self.exitAction = QAction(QIcon( os.path.join(ico_path, 'exit24.png') ), 'Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.close)
        #-------------------------------------------------------------

        self.ipyConsoleAction = QAction(QIcon( os.path.join(ico_path, 'ipy-console-24.png') ), 'Jupyter Console', self)
        self.ipyConsoleAction.setShortcut('Alt+S')
        self.ipyConsoleAction.setStatusTip('Launch Jupyter Console')
        self.ipyConsoleAction.triggered.connect(self.parent.launch_jupyter_console_slot)

        #-------------------------------------------------------------
        self.ipyQtConsoleAction = QAction(QIcon( os.path.join(ico_path, 'ipy-qtconsole-24.png') ), 'Jupyter QtConsole', self)
        self.ipyQtConsoleAction.setShortcut('Alt+T')
        self.ipyQtConsoleAction.setStatusTip('Launch Jupyter QtConsole')
        self.ipyQtConsoleAction.triggered.connect(self.parent.launch_jupyter_qtconsole_slot)
        
        #-------------------------------------------------------------
        self.vstreamAction = self.CheckedAction('play-24.png', 'pause-24.png', 'Start/Stop Video', self)
        self.vstreamAction.setShortcut('F5')
        self.vstreamAction.trigAction()

        #-------------------------------------------------------------
        self.agcAction = self.CheckedAction('automatic-off-24.png', 'automatic-on-24.png', 'Automatic Gain Control', self)
        self.agcAction.setShortcut('F6')
        self.agcAction.trigAction()

        #-------------------------------------------------------------
        self.zffAction = QAction(QIcon( os.path.join(ico_path, 'zoom-fit-frame-24.png') ), 'Fit Frame', self)
        self.zffAction.setShortcut('Ctrl+1')
        self.zffAction.setStatusTip('Zoom: Fit Frame. Hotkey: "Ctrl+1"')
        self.zffAction.triggered.connect(self.main_view.fit_scene_to_view)
        
        #-------------------------------------------------------------
        self.sdlgAction = QAction(QIcon( os.path.join(ico_path, 'settings-24.png') ), 'Settings', self)
        self.sdlgAction.setShortcut('F12')
        self.sdlgAction.setStatusTip('Edit settings')
        self.sdlgAction.triggered.connect(self.edit_settings)
        
        #-------------------------------------------------------------
        self.rstatAction = QAction(QIcon( os.path.join(ico_path, 'reset-stat-24.png') ), 'Reset Statistics', self)
        self.rstatAction.setShortcut('F11')
        self.rstatAction.setStatusTip('Reset statistics. Hotkey: "F11"')
        #self.rstatAction.triggered.connect(self.main_view.reset_statistics)

    #---------------------------------------------------------------------------
    def setup_menu(self):
        self.menubar = self.menuBar()
        self.controlMenu = self.menubar.addMenu('&Control')
        self.controlMenu.addAction(self.ipyConsoleAction)
        self.controlMenu.addAction(self.ipyQtConsoleAction)
        self.controlMenu.addAction(self.vstreamAction)
        self.controlMenu.addAction(self.agcAction)
        self.controlMenu.addAction(self.rstatAction)
        self.controlMenu.addAction(self.sdlgAction)
        self.controlMenu.addAction(self.exitAction)
        
        self.viewMenu = self.menubar.addMenu('&Zoom')
        self.viewMenu.addAction(self.zffAction)
        
    #---------------------------------------------------------------------------
    def setup_toolbar(self):
        self.toolbar = self.addToolBar('MainToolbar')
        self.toolbar.setObjectName('main-toolbar')
        self.toolbar.addAction(self.exitAction)        
        self.toolbar.addAction(self.ipyConsoleAction)        
        self.toolbar.addAction(self.ipyQtConsoleAction)        
        self.toolbar.addAction(self.vstreamAction)
        self.toolbar.addAction(self.agcAction)
        self.toolbar.addAction(self.zffAction)
        self.toolbar.addAction(self.sdlgAction)
        self.toolbar.addAction(self.rstatAction)

    #---------------------------------------------------------------------------
    def edit_settings(self):
        self.settings_dialog.show()
        
    #---------------------------------------------------------------------------
    def setup_main_scene(self):
        self.main_scene = GraphicsScene(self)
        self.main_scene.setBackgroundBrush(QColor(0x20, 0x20, 0x20))
        self.no_vstream_pixmap = QPixmap(FRAME_SIZE_X, FRAME_SIZE_Y)
        self.no_vstream_pixmap.fill(QColor(0x00,0x00,0x40,255))
        self.pixmap_item = self.init_pixmap_item(FRAME_SIZE_X, FRAME_SIZE_Y, self.no_vstream_pixmap, 1)
        self.main_scene.addItem(self.pixmap_item)
        self.img = self.pixmap_item.pixmap().toImage()

        self.main_view = GraphicsView(self.main_scene, self)
        self.main_view.setFrameStyle(QFrame.NoFrame)
    
    #---------------------------------------------------------------------------
    def create_log_window(self):
        self.log = QDockWidget('Log', self, Qt.WindowCloseButtonHint)
        self.log.setObjectName('Log Window')
        self.log.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.log.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.log_widget = LogWidget(self)
        self.log.setWidget(self.log_widget)
        
    #---------------------------------------------------------------------------
    def create_telemetry_window(self):
        self.telemetry = QDockWidget('Telemetry', self, Qt.WindowCloseButtonHint)
        self.telemetry.setObjectName('Telemetry Window')
        self.telemetry.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.telemetry.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.telemetry_widget = TelemetryWidget(self)
        self.telemetry.setWidget(self.telemetry_widget)

    #---------------------------------------------------------------------------
    def initUI(self):

        #----------------------------------------------------
        #
        #    Main Window
        #
        self.setup_main_scene()
        self.create_log_window()
        self.create_telemetry_window()

        self.addDockWidget(Qt.BottomDockWidgetArea, self.log)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.telemetry)
        self.setCentralWidget(self.main_view)
        
        self.restore_main_window()

        self.setup_actions()
        self.setup_menu()
        self.setup_toolbar()

        self.set_title()
        
        self.settings_dialog = settings.SettingsDialog(self.parent.settings, self)

        self.statusBar().showMessage('Ready')
        
        self.show()
        if self.parent.settings['Frame']['ZoomFit']:
            self.main_view.fit_scene_to_view()
        
    #---------------------------------------------------------------------------
    def update_status_bar(self):
        text = 'Zoom: {:.1f} | View: {:d} {:d} | Scene: {:d} {:d} | Value: {}'.format(self.zoom,
                                                                          self.view_cpos_x,  self.view_cpos_y,
                                                                          self.scene_cpos_x, self.scene_cpos_y, self.pixval)
        self.statusBar().showMessage(text)
        
    #---------------------------------------------------------------------------
    def update_zoom(self, zoom):
        self.zoom = zoom
        
    #---------------------------------------------------------------------------
    def update_cursor_pos(self, vx, vy, sx, sy, pval):
        self.view_cpos_x  = vx
        self.view_cpos_y  = vy
        self.scene_cpos_x = sx
        self.scene_cpos_y = sy
        self.pixval       = pval
        self.update_status_bar()
                
#-------------------------------------------------------------------------------
class LogWidget(QTableWidget):

    #-----------------------------------------------------------------
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

    #-----------------------------------------------------------------
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
class TelemetryWidget(QTableWidget):

    #-----------------------------------------------------------------
    def __init__(self, parent):
        super().__init__(4, 7, parent)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # select whole row
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)   # disable edit cells
        self.horizontalHeader().resizeSection(0, 200)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setDefaultSectionSize(20)
        self.setTabKeyNavigation(False)
        self.setAlternatingRowColors(True)
        self.setHorizontalHeaderLabels( ['Name', 'Value', 'Mean', 'Min', 'Max', 'SDev', 'Frame Count'] )

        self.setRowCount(4)
        

        self.DEV = 0
        self.SDC = 1
        
        self.NAME  = 0
        self.VALUE = 1
        self.MEAN  = 2
        self.MIN   = 3
        self.MAX   = 4
        self.SDEV  = 5
        self.FCNT  = 6

        self.setItem(self.DEV, self.NAME, self.create_item('Device Camera FPS') )
        self.setItem(self.SDC, self.NAME, self.create_item('SD Camera FPS') )

        self.setItem(self.DEV, self.VALUE, self.create_item() )
        self.setItem(self.DEV, self.MEAN,  self.create_item() )
        self.setItem(self.DEV, self.MIN,   self.create_item() )
        self.setItem(self.DEV, self.MAX,   self.create_item() )
        self.setItem(self.DEV, self.SDEV,  self.create_item() )
        self.setItem(self.DEV, self.FCNT,  self.create_item() )
        
        self.setItem(self.SDC, self.VALUE, self.create_item() )
        self.setItem(self.SDC, self.MEAN,  self.create_item() )
        self.setItem(self.SDC, self.MIN,   self.create_item() )
        self.setItem(self.SDC, self.MAX,   self.create_item() )
        self.setItem(self.SDC, self.SDEV,  self.create_item() )
        self.setItem(self.SDC, self.FCNT,  self.create_item() )

    #-----------------------------------------------------------------
    def create_item(self, val=''):

        item = QTableWidgetItem(val)
        item.setForeground(QColor('#F0F0F0'))
        item.setTextAlignment(Qt.AlignTop)
        
        return item

    #-----------------------------------------------------------------
    def update_slot(self, msg):

        if msg[0] == 0:
            dev_fps = msg[1]

            self.item(self.DEV, self.VALUE).setText ('{:.3f}'.format(dev_fps.value))
            self.item(self.DEV, self.MEAN).setText  ('{:.3f}'.format(dev_fps.mean))
            self.item(self.DEV, self.MIN).setText   ('{:.3f}'.format(dev_fps.min))
            self.item(self.DEV, self.MAX).setText   ('{:.3f}'.format(dev_fps.max))
            self.item(self.DEV, self.SDEV).setText  ('{:.3f}'.format(dev_fps.sdev))
            self.item(self.DEV, self.FCNT).setText  (   '{:}'.format(dev_fps.frame_count))

        if msg[0] == 1:
            sdc_fps = msg[1]

            self.item(self.SDC, self.VALUE).setText ('{:.3f}'.format(sdc_fps.value))
            self.item(self.SDC, self.MEAN).setText  ('{:.3f}'.format(sdc_fps.mean))
            self.item(self.SDC, self.MIN).setText   ('{:.3f}'.format(sdc_fps.min))
            self.item(self.SDC, self.MAX).setText   ('{:.3f}'.format(sdc_fps.max))
            self.item(self.SDC, self.SDEV).setText  ('{:.3f}'.format(sdc_fps.sdev))
            self.item(self.SDC, self.FCNT).setText  (   '{:}'.format(sdc_fps.frame_count))

#-------------------------------------------------------------------------------
        
