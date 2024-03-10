
#-------------------------------------------------------------------------------


from PyQt5.Qt        import Qt

from PyQt5.QtWidgets import (QWidget, QDialog, QLayout, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QCheckBox, QLabel, QLineEdit, QDialogButtonBox,
                             QComboBox, QFontComboBox, QAction)

from PyQt5.QtCore    import QSettings, pyqtSignal, QObject, QEvent, QRect, QSize

from PyQt5.QtGui     import QFont

#-------------------------------------------------------------------------------
class TSettingsDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        
        self.setWindowTitle('Settings')
        self.resize(550, 480)
        
        self.horizontalLayoutWidget = QWidget(self)
        self.horizontalLayoutWidget.setGeometry(QRect(10, 20, 530, 390))

        #-------------------------------------------------------------
        #
        #    Frame
        #
        self.ltMain = QHBoxLayout(self.horizontalLayoutWidget)
        self.ltMain.setSizeConstraint(QLayout.SetNoConstraint)
        self.ltMain.setContentsMargins(0, 0, 0, 0)

        self.gbFrame = QGroupBox(self.horizontalLayoutWidget)
        self.gbFrame.setTitle('Frame')
        self.gbFrame.setEnabled(True)

        self.cbZoomFit = QCheckBox(self.gbFrame)
        self.cbZoomFit.setText('Zoom Fit')
        self.cbZoomFit.setGeometry(QRect(10, 30, 100, 24))

        self.ltMain.addWidget(self.gbFrame)
        
        #-------------------------------------------------------------
        #
        #    IPython console
        #
        self.gbIPycon = QGroupBox(self.horizontalLayoutWidget)
        self.gbIPycon.setTitle('IPython Console')

        #    Geometry Origin
        self.gbIPyconOrigin = QGroupBox(self.gbIPycon)
        self.gbIPyconOrigin.setEnabled(True)
        self.gbIPyconOrigin.setGeometry(QRect(10, 30, 150, 90))
        self.gbIPyconOrigin.setTitle('Origin')
        
        self.lbIPyconX = QLabel(self.gbIPyconOrigin)
        self.lbIPyconX.setGeometry(QRect(10, 30, 10, 24))
        self.lbIPyconX.setText('X')

        self.leIPyconX = QLineEdit(self.gbIPyconOrigin)
        self.leIPyconX.setGeometry(QRect(10, 50, 60, 24))
        self.leIPyconX.setText('1200')

        self.lbIPyconY = QLabel(self.gbIPyconOrigin)
        self.lbIPyconY.setGeometry(QRect(80, 30, 10, 24))
        self.lbIPyconY.setText('Y')

        self.leIPyconY = QLineEdit(self.gbIPyconOrigin)
        self.leIPyconY.setGeometry(QRect(80, 50, 60, 24))
        self.leIPyconY.setText('0')
        
        #    Geometry Size
        self.gbIPyconSize = QGroupBox(self.gbIPycon)
        self.gbIPyconSize.setGeometry(QRect(10, 130, 150, 90))
        self.gbIPyconSize.setTitle('Size')

        self.lbIPyconWidth = QLabel(self.gbIPyconSize)
        self.lbIPyconWidth.setGeometry(QRect(10, 30, 50, 24))
        self.lbIPyconWidth.setText('Width')
        
        self.leIPyconWidth = QLineEdit(self.gbIPyconSize)
        self.leIPyconWidth.setGeometry(QRect(10, 50, 60, 24))
        self.leIPyconWidth.setText('150')
        
        self.lbIPyconHeight = QLabel(self.gbIPyconSize)
        self.lbIPyconHeight.setGeometry(QRect(80, 30, 60, 24))
        self.lbIPyconHeight.setText('Height')
        
        self.leIPyconHeight = QLineEdit(self.gbIPyconSize)
        self.leIPyconHeight.setGeometry(QRect(80, 50, 60, 24))
        self.leIPyconHeight.setText('69')

        self.ltMain.addWidget(self.gbIPycon)
        
        #-------------------------------------------------------------
        #
        #    Jupyter Qt console
        #
        self.gbQtcon     = QGroupBox(self.horizontalLayoutWidget)
        self.gbQtcon.setTitle('Qt Console')

        #    Font
        self.gbQtconFont = QGroupBox(self.gbQtcon)
        self.gbQtconFont.setGeometry(QRect(10, 230, 200, 150))
        self.gbQtconFont.setTitle('Font')

        self.lbQtconFontName = QLabel(self.gbQtconFont)
        self.lbQtconFontName.setGeometry(QRect(10, 20, 70, 30))
        self.lbQtconFontName.setText('Name')

        font = QFont()
        font.setFamily(u"DejaVu Sans Mono")
        font.setPointSize(14)
        
        self.cboxQtconFontName = QFontComboBox(self.gbQtconFont)
        self.cboxQtconFontName.setGeometry(QRect(10, 45, 180, 24))
        self.cboxQtconFontName.setContextMenuPolicy(Qt.PreventContextMenu)
        self.cboxQtconFontName.setCurrentFont(font)

        self.lbQtconFontSize = QLabel(self.gbQtconFont)
        self.lbQtconFontSize.setGeometry(QRect(10, 75, 70, 30))
        self.lbQtconFontSize.setText('Size')
        
        self.cboxQtconFontSize = QComboBox(self.gbQtconFont)
        self.cboxQtconFontSize.setGeometry(QRect(10, 100, 100, 24))
        self.cboxQtconFontSize.setEditable(True)
        self.cboxQtconFontSize.setCurrentText('14')

        #    Geometry Origin
        self.gbQtconOrigin = QGroupBox(self.gbQtcon)
        self.gbQtconOrigin.setEnabled(True)
        self.gbQtconOrigin.setGeometry(QRect(10, 30, 150, 90))
        self.gbQtconOrigin.setTitle('Origin')

        self.lbQtconX = QLabel(self.gbQtconOrigin)
        self.lbQtconX.setGeometry(QRect(10, 30, 10, 24))
        self.lbQtconX.setText('X')
        
        self.leQtconX = QLineEdit(self.gbQtconOrigin)
        self.leQtconX.setGeometry(QRect(10, 50, 60, 24))
        self.leQtconX.setText('1200')

        self.lbQtconY = QLabel(self.gbQtconOrigin)
        self.lbQtconY.setGeometry(QRect(80, 30, 10, 24))
        self.lbQtconY.setText('Y')
        
        self.leQtconY = QLineEdit(self.gbQtconOrigin)
        self.leQtconY.setGeometry(QRect(80, 50, 60, 24))
        self.leQtconY.setText('0')

        #    Geometry Size
        self.gbQtconSize = QGroupBox(self.gbQtcon)
        self.gbQtconSize.setGeometry(QRect(10, 130, 150, 90))
        self.gbQtconSize.setTitle('Size')

        self.lbQtconWidth = QLabel(self.gbQtconSize)
        self.lbQtconWidth.setGeometry(QRect(10, 30, 50, 24))
        self.lbQtconWidth.setText('Width')

        self.leQtconWidth = QLineEdit(self.gbQtconSize)
        self.leQtconWidth.setGeometry(QRect(10, 50, 60, 24))
        self.leQtconWidth.setText('150')

        self.lbIQtonHeight = QLabel(self.gbQtconSize)
        self.lbIQtonHeight.setGeometry(QRect(80, 30, 60, 24))
        self.lbIQtonHeight.setText('Height')

        self.leQtconHeight = QLineEdit(self.gbQtconSize)
        self.leQtconHeight.setGeometry(QRect(80, 50, 60, 24))
        self.leQtconHeight.setText('69')

        self.ltMain.addWidget(self.gbQtcon)

        #-------------------------------------------------------------
        #
        #    Button box
        #
        self.ButtonBox = QDialogButtonBox(self)
        self.ButtonBox.setGeometry(QRect(190, 430, 170, 32))
        self.ButtonBox.setOrientation(Qt.Horizontal)
        self.ButtonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        
        self.ButtonBox.accepted.connect(self.save_settings)
        self.ButtonBox.rejected.connect(self.cancel)

        self.ltMain.setStretch(0, 14)
        self.ltMain.setStretch(1, 20)
        self.ltMain.setStretch(2, 26)

    #-----------------------------------------------------------------
    def save_settings(self):
        print('save settings')
        Settings = QSettings('camlab', 'sdcam')
        Settings.setValue('component-view', self.CmpViewTable.data_dict())

        curr_file = CmpMgr.curr_file_path()
        self.Parent.CmpTable.reload_file(curr_file)

        self.close()
    #-----------------------------------------------------------------
    def cancel(self):
        print('close settings dialog')
        self.close()

#-------------------------------------------------------------------------------

