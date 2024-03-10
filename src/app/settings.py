
#-------------------------------------------------------------------------------


from PyQt5.Qt        import Qt
from PyQt5.QtWidgets import (QWidget, QDialog, QLayout, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QCheckBox, QLabel, QLineEdit, QDialogButtonBox,
                             QComboBox, QFontComboBox, QAction)
from PyQt5.QtCore    import QSettings, pyqtSignal, QObject, QEvent, QRect, QSize
from PyQt5.QtGui     import QFont

from logger import logger as lg


#-------------------------------------------------------------------------------
app_settings = \
{
    'Frame'  : { 'ZoomFit' : True },
    'IPycon' :
    {
        'OrgX'   : '0',
        'OrgY'   : '0',
        'Width'  : '100',
        'Height' : '100'
    },
    'Qtcon' :
    {
        'OrgX'     : '0',
        'OrgY'     : '0',
        'Width'    : '100',
        'Height'   : '100',
        'FontName' : 'DejaVu Sans Mono',
        'FontSize' : '10'
    }
}
#-------------------------------------------------------------------------------
def read(key):
    Settings = QSettings('cam-lab', 'sdcam')
    settings = Settings.value(key)

    return settings

#-------------------------------------------------------------------------------
class TSettingsDialog(QDialog):

    def __init__(self, settings, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.setModal(True)
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
        self.cbZoomFit.setCheckState(Qt.Checked if settings['Frame']['ZoomFit'] else Qt.Unchecked)
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
        self.leIPyconX.setText(settings['IPycon']['OrgX'])

        self.lbIPyconY = QLabel(self.gbIPyconOrigin)
        self.lbIPyconY.setGeometry(QRect(80, 30, 10, 24))
        self.lbIPyconY.setText('Y')

        self.leIPyconY = QLineEdit(self.gbIPyconOrigin)
        self.leIPyconY.setGeometry(QRect(80, 50, 60, 24))
        self.leIPyconY.setText(settings['IPycon']['OrgY'])
        
        #    Geometry Size
        self.gbIPyconSize = QGroupBox(self.gbIPycon)
        self.gbIPyconSize.setGeometry(QRect(10, 130, 150, 90))
        self.gbIPyconSize.setTitle('Size')

        self.lbIPyconWidth = QLabel(self.gbIPyconSize)
        self.lbIPyconWidth.setGeometry(QRect(10, 30, 50, 24))
        self.lbIPyconWidth.setText('Width')
        
        self.leIPyconWidth = QLineEdit(self.gbIPyconSize)
        self.leIPyconWidth.setGeometry(QRect(10, 50, 60, 24))
        self.leIPyconWidth.setText(settings['IPycon']['Width'])
        
        self.lbIPyconHeight = QLabel(self.gbIPyconSize)
        self.lbIPyconHeight.setGeometry(QRect(80, 30, 60, 24))
        self.lbIPyconHeight.setText('Height')
        
        self.leIPyconHeight = QLineEdit(self.gbIPyconSize)
        self.leIPyconHeight.setGeometry(QRect(80, 50, 60, 24))
        self.leIPyconHeight.setText(settings['IPycon']['Height'])

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
        font.setFamily(settings['Qtcon']['FontName'])
        font.setPointSize(int(settings['Qtcon']['FontSize']))
        
        self.cboxQtconFontName = QFontComboBox(self.gbQtconFont)
        self.cboxQtconFontName.setGeometry(QRect(10, 45, 180, 24))
        self.cboxQtconFontName.setContextMenuPolicy(Qt.PreventContextMenu)
        self.cboxQtconFontName.setCurrentFont(font)

        self.lbQtconFontSize = QLabel(self.gbQtconFont)
        self.lbQtconFontSize.setGeometry(QRect(10, 75, 70, 30))
        self.lbQtconFontSize.setText('Size')
        
        self.cboxQtconFontSize = QComboBox(self.gbQtconFont)
        self.cboxQtconFontSize.setGeometry(QRect(10, 100, 50, 24))
        self.cboxQtconFontSize.setEditable(True)
        self.cboxQtconFontSize.setInsertPolicy(QComboBox.NoInsert)
        self.cboxQtconFontSize.addItems([str(i) for i in  [8, 9, 10, 11, 12, 14, 16, 18]])
        self.cboxQtconFontSize.setCurrentText(settings['Qtcon']['FontSize'])

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
        self.leQtconX.setText(settings['Qtcon']['OrgX'])

        self.lbQtconY = QLabel(self.gbQtconOrigin)
        self.lbQtconY.setGeometry(QRect(80, 30, 10, 24))
        self.lbQtconY.setText('Y')
        
        self.leQtconY = QLineEdit(self.gbQtconOrigin)
        self.leQtconY.setGeometry(QRect(80, 50, 60, 24))
        self.leQtconY.setText(settings['Qtcon']['OrgY'])

        #    Geometry Size
        self.gbQtconSize = QGroupBox(self.gbQtcon)
        self.gbQtconSize.setGeometry(QRect(10, 130, 150, 90))
        self.gbQtconSize.setTitle('Size')

        self.lbQtconWidth = QLabel(self.gbQtconSize)
        self.lbQtconWidth.setGeometry(QRect(10, 30, 50, 24))
        self.lbQtconWidth.setText('Width')

        self.leQtconWidth = QLineEdit(self.gbQtconSize)
        self.leQtconWidth.setGeometry(QRect(10, 50, 60, 24))
        self.leQtconWidth.setText(settings['Qtcon']['Width'])

        self.lbIQtonHeight = QLabel(self.gbQtconSize)
        self.lbIQtonHeight.setGeometry(QRect(80, 30, 60, 24))
        self.lbIQtonHeight.setText('Height')

        self.leQtconHeight = QLineEdit(self.gbQtconSize)
        self.leQtconHeight.setGeometry(QRect(80, 50, 60, 24))
        self.leQtconHeight.setText(settings['Qtcon']['Height'])

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
        lg.info('save settings')
        settings = self.parent.parent.settings

        settings['Frame']['ZoomFit'] = True if self.cbZoomFit.checkState() == Qt.Checked else False
        settings['IPycon']['OrgX']   = self.leIPyconX.text()
        settings['IPycon']['OrgY']   = self.leIPyconY.text()
        settings['IPycon']['Width']  = self.leIPyconWidth.text()
        settings['IPycon']['Height'] = self.leIPyconHeight.text()

        settings['Qtcon']['OrgX']    = self.leQtconX.text()
        settings['Qtcon']['OrgY']    = self.leQtconY.text()
        settings['Qtcon']['Width']   = self.leQtconWidth.text()
        settings['Qtcon']['Height']  = self.leQtconHeight.text()

        settings['Qtcon']['FontName'] = self.cboxQtconFontName.currentFont().family()
        settings['Qtcon']['FontSize'] = self.cboxQtconFontSize.currentText()

        Settings = QSettings('cam-lab', 'sdcam')
        Settings.setValue('Application/Settings', settings)
        self.close()
        
    #-----------------------------------------------------------------
    def cancel(self):
        lg.info('close settings dialog')
        
        self.close()

#-------------------------------------------------------------------------------

