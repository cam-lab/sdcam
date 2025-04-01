#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: GUI Dashboard
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

import numpy as np

from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, QHBoxLayout, QSplitter)

from PyQt5.QtWidgets import (QHeaderView, QAbstractItemView, QTreeWidget, QTreeWidgetItem, QComboBox, QStyledItemDelegate)
from PyQt5.QtGui     import QCursor, QIcon, QImage, QPixmap, QColor, QTransform, QPen, QBrush, QKeySequence
from PyQt5.QtCore    import pyqtSignal, QObject, QEvent
from PyQt5.QtCore    import QT_VERSION_STR

from QCustomPlot_PyQt5 import *

from logger   import logger as lg

#-------------------------------------------------------------------------------
class ComboBox(QComboBox):

    def __init__(self, parent):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, e):
        key = e.key()
        mod = e.modifiers()
        if key == Qt.Key_Down or key == Qt.Key_Up:
            if not mod:
                QApplication.sendEvent( self.parent(), e )
                return
            elif mod == Qt.AltModifier:
                self.showPopup()

        QComboBox.keyPressEvent(self, e)


    def set_index(self, text):
        items = [self.itemText(i) for i in range(self.count()) ]
        self.setCurrentIndex( items.index(text) )
        
#-------------------------------------------------------------------------------
class DashboardItemDelegate(QStyledItemDelegate):

    TEXT_DELEGATE = 0
    CBOX_DELEGATE = 1

    #----------------------------------------------------------------
    def __init__(self, parent):
        super().__init__(parent)
        self.editors = {}
    #----------------------------------------------------------------
    def clear_editor_data(self):
        self.editors = {}
    #----------------------------------------------------------------
    def add_editor_data(self, name, editor_type, editor_data = []):
        self.editors[name] = [editor_type, editor_data]
        
    #----------------------------------------------------------------
    def createEditor(self, parent, option, idx):
        if idx.column() == 1:
            name = idx.sibling(idx.row(), 0).data()
            etype = self.editors[name][0]
            if etype == self.TEXT_DELEGATE:
                editor = QStyledItemDelegate.createEditor(self, parent, option, idx)
                return editor
            else:
                editor = ComboBox(parent)
                editor.setEnabled(True)
                editor.setEditable(False)
                editor.addItems( self.editors[name][1] )
                return editor
    #----------------------------------------------------------------
    def setEditorData(self, editor, idx):
        #print(editor.metaObject().className() )
        name = idx.sibling(idx.row(), 0).data()
        if self.editors[name][0] == self.TEXT_DELEGATE:
            QStyledItemDelegate.setEditorData(self, editor, idx)
        else:
            value = idx.model().data(idx, Qt.EditRole)
            editor.set_index(value)
            
    #----------------------------------------------------------------
    def setModelData(self, editor, model, idx):
        name = idx.sibling(idx.row(), 0).data()
        if self.editors[name][0] == self.TEXT_DELEGATE:
            QStyledItemDelegate.setModelData(self, editor, model, idx)
        else:
            value = editor.currentText()
            values = self.editors[name][1]
            if value not in values:
                values.append(value)

            QStyledItemDelegate.setModelData(self, editor, model, idx)
            
    #----------------------------------------------------------------
    def paint(self, painter, option, idx):
        painter.save()

        # set background color
        painter.setPen(QPen(Qt.NoPen))

        if idx.column() == 0:
            painter.setBrush(QBrush(QColor('#393939')))
        else:
            painter.setBrush(QBrush(Qt.transparent))

        if not idx.parent().isValid():
            painter.setBrush(QBrush(QColor(0xFF, 0xDC, 0xA4) ) )

        painter.drawRect(option.rect)

        # draw the rest
        QStyledItemDelegate.paint(self, painter, option, idx)

        painter.restore()

#-------------------------------------------------------------------------------
class DashBoardParamsWidget(QTreeWidget):

    colNAME = 0
    colDATA = 1
    
    #-----------------------------------------------------------------
    def __init__(self, parent):
        super().__init__(parent)
        
        sdc = parent.sdc

        self.setIndentation(16)
        self.setColumnCount(2)
        self.header().resizeSection(2, 10)
        self.header().setSectionResizeMode(self.colNAME, QHeaderView.Interactive)
        self.setHeaderLabels( ('Name', 'Value') );
        self.dac_items = self.addParent(self, 0, 'DAC', '')
        self.det_items = self.addParent(self, 0, 'DET', '')
        
        self.ItemsDelegate = DashboardItemDelegate(self)
        self.setItemDelegate(self.ItemsDelegate)

        for idx, i in enumerate(sdc.dac):
            item = self.addChild(self.dac_items, i, sdc.dac[i][1])
            if idx == 0:
                self.setCurrentItem(item)
                
            self.ItemsDelegate.add_editor_data(i, self.ItemsDelegate.TEXT_DELEGATE)
        
        for idx, i in enumerate(sdc.det):
            item = self.addChild(self.det_items, i, list(sdc.det[i].keys())[0])
            self.ItemsDelegate.add_editor_data(i, self.ItemsDelegate.CBOX_DELEGATE, sdc.det[i].keys())

        self.itemActivated.connect(self.item_activated)
        
    #---------------------------------------------------------------------------
    def addParent(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        item.setExpanded (True)
        item.setFlags(Qt.ItemIsEnabled)
        return item

    #---------------------------------------------------------------------------
    def addChild(self, parent, title, data, flags=Qt.NoItemFlags):
        item = QTreeWidgetItem(parent, [title])
        item.setData(self.colDATA, Qt.DisplayRole, data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | flags)
        return item

    #---------------------------------------------------------------------------
    def item_activated(self, item, col):
        self.editItem(item, self.colDATA)
        
    #---------------------------------------------------------------------------
    def curr_item_changed(self, item, prev):
        idx    = self.indexFromItem(prev, self.colDATA)
        editor = self.indexWidget(idx)

        if editor:
            #print(editor)
            self.commitData(editor)
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)

        self.editItem(item, self.colDATA)
        self.item_clicked(item, self.colNAME)
    
    #---------------------------------------------------------------------------
    def update(self, params):
        pass

    #---------------------------------------------------------------------------


#-------------------------------------------------------------------------------
class HistogramWidget(QCustomPlot):
    #-----------------------------------------------------------------
    def __init__(self, parent, color):
        super().__init__(parent)
        
        self.graph = self.addGraph()
        self.graph.setPen(QPen( color.lighter(100) ) )
        self.graph.setBrush(QBrush(color) )
        
        self.rescaleAxes()
        self.setInteraction(QCP.iRangeDrag)
        self.setInteraction(QCP.iRangeZoom)
        self.setInteraction(QCP.iSelectPlottables)
        
        self.setBackground(QColor(0x26, 0x26, 0x24, 255))
        self.xAxis.setTickLabelColor(QColor(255, 255, 255, 255))
        self.yAxis.setTickLabelColor(QColor(255, 255, 255, 255))
        
        self.max = 0
        
    def draw(self, h, thld=1):
        x    = np.arange(h.org, h.top)
        y    = h.data[h.org:h.top]
        self.graph.setData(x, y)
        
        if h.max > 0.95*self.max or h.max < 0.75*self.max:
            self.max = h.max*1.1
            self.rescaleAxes()

        self.replot()

    def mouseDoubleClickEvent(self, event):
        self.rescaleAxes()


#-------------------------------------------------------------------------------
class HistogramWidget(QCustomPlot):
    #-----------------------------------------------------------------
    def __init__(self, parent, color):
        super().__init__(parent)

        self.graph = self.addGraph()
        self.graph.setPen(QPen( color.lighter(100) ) )
        self.graph.setBrush(QBrush(color) )

        self.rescaleAxes()
        self.setInteraction(QCP.iRangeDrag)
        self.setInteraction(QCP.iRangeZoom)
        self.setInteraction(QCP.iSelectPlottables)

        self.setBackground(QColor(0x26, 0x26, 0x24, 255))
        self.xAxis.setTickLabelColor(QColor(255, 255, 255, 255))
        self.yAxis.setTickLabelColor(QColor(255, 255, 255, 255))

        self.max = 0

    def draw(self, h, thld=1):
        x    = np.arange(h.org, h.top)
        y    = h.data[h.org:h.top]
        self.graph.setData(x, y)

        if h.max > 0.95*self.max or h.max < 0.75*self.max:
            self.max = h.max*1.1
            self.rescaleAxes()

        self.replot()

    def mouseDoubleClickEvent(self, event):
        self.rescaleAxes()

#-------------------------------------------------------------------------------
        
