

from PyQt5.QtCore    import QObject, pyqtSignal

#-------------------------------------------------------------------------------
class TLogger(QObject):
    log_signal = pyqtSignal( str )

    def __init__(self):
        super().__init__()

    def info(self, s):
        self.log_signal.emit(s)

#-------------------------------------------------------------------------------

Logger = TLogger()

#-------------------------------------------------------------------------------

