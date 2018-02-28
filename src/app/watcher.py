

import os
import time
import threading

from   PyQt5.QtCore import QObject, pyqtSignal
from   logger import logger as lg

PERIOD = 0.25

#-------------------------------------------------------------------------------
class TWatcher(QObject):

    file_changed_signal = pyqtSignal( str )

    #-------------------------------------------------------    
    def __init__(self, fname):
        super().__init__()
        self.stamp = 0
        self.fname = fname

    #-------------------------------------------------------    
    def processing(self):
        stamp = os.stat(self.fname).st_mtime
        if stamp != self.stamp:
            self.stamp = stamp
            self.file_changed_signal.emit(self.fname)
        
#-------------------------------------------------------------------------------
class TWatcherThread(threading.Thread):

    #-------------------------------------------------------
    def __init__(self, log_file, name='Watcher Thread' ):
        #super().__init__(daemon=True)
        super().__init__()
        self._finish_event = threading.Event()
        self.watcher = TWatcher(log_file)

    #-------------------------------------------------------
    def finish(self):
        self._finish_event.set()
        lg.info('Watcher Thread pending to finish')

    #-------------------------------------------------------
    def run(self):
        while True:
            time.sleep(PERIOD)
            self.watcher.processing()
            if self._finish_event.is_set():
                return
            
#-------------------------------------------------------------------------------
    
