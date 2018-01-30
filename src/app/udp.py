

import threading
from   socket import *
import queue
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal

from logger import logger as lg


host_ip   = '192.168.10.1'
device_ip = '192.168.10.3'
udp_port  = 50014

command_queue = queue.Queue()

vhex = np.vectorize(hex)

#-------------------------------------------------------------------------------
class TSocket(QObject):

    def __init__(self):
        super().__init__()

        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.settimeout(0.5)
        self.sock.bind( (host_ip, udp_port) )

    def processing(self, data):
        self.sock.sendto(data, (device_ip, udp_port))
        try:
            res = np.frombuffer( self.sock.recv(1472), dtype=np.uint16)
            lg.info(vhex(res))
        except timeout:
            lg.info('socket timeout')

#-------------------------------------------------------------------------------
class TSocketThread(threading.Thread):

    def __init__(self, name='Socket Thread' ):
        super().__init__()
        self._sock = TSocket()

    def finish(self):
        lg.info('Socket Thread pending to finish')
        command_queue.put(None)

    def run(self):
        lg.info('udp socket thread::run')
        while True:
            item = command_queue.get()
            if item:
                self._sock.processing(item[0])
            else:
                return
            
        ld.info('udp socket thread::run exit')
            
#-------------------------------------------------------------------------------
    
