

import os
import logging

from PyQt5.QtCore    import QObject, pyqtSignal

#-------------------------------------------------------------------------------
class TLogger(QObject):
    log_signal = pyqtSignal( str )

    def __init__(self):
        super().__init__()

    def info(self, s):
        self.log_signal.emit(s)

#-------------------------------------------------------------------------------

#Logger = TLogger()

LOG_FILE = 'sdcam.log'

#-------------------------------------------------------------------------------
logging.basicConfig(filename=LOG_FILE,
                    filemode='w',
                    level=logging.DEBUG, 
                    format='%(asctime)s %(module)-9s %(levelname)-7s : %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger('default')
#-------------------------------------------------------------------------------

