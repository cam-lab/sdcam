#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: Logger functionality
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

import os
import logging

from pathlib      import Path
from PyQt5.QtCore import QObject, pyqtSignal

#-------------------------------------------------------------------------------
class TLogger(QObject):
    log_signal = pyqtSignal( str )

    def __init__(self):
        super().__init__()

    def info(self, s):
        self.log_signal.emit(s)

#-------------------------------------------------------------------------------

LOG_FILE = Path('log') / 'sdcam.log'

#-------------------------------------------------------------------------------
def setup_logger(lvl):
    levels = {
        'debug'    : logging.DEBUG,
        'info'     : logging.INFO,
        'warning'  : logging.WARNING,
        'error'    : logging.ERROR
    }
    logging.basicConfig(filename=LOG_FILE,
                        filemode='w',
                        level=levels[lvl], 
                        format='%(asctime)s %(module)-12s %(levelname)-7s : %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger('default')
#-------------------------------------------------------------------------------

