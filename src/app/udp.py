#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: UDP Socket for control
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

import threading
from   socket import *
import queue
import time

import numpy as np
from   PyQt5.QtCore import QObject, pyqtSignal

from   logger import logger as lg


HOST_IP   = '192.168.10.1'
DEVICE_IP = '192.168.10.10'

LB_PORT   = 50000
CAM_PORT  = 50001
DRC_PORT  = 50002

command_queue = queue.Queue()

vhex = np.vectorize(hex)

#-------------------------------------------------------------------------------
class Socket(QObject):

    #-------------------------------------------------------
    def __init__(self, host_ip, port, device_ip):
        super().__init__()
        
        self.dev_ip = device_ip
        self.port   = port

        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.settimeout(0.5)
        self.sock.bind( (host_ip, port) )

    #-------------------------------------------------------
    def processing(self, data):
        try:
            self.sock.sendto(data, (self.dev_ip, self.port))
            try:
                res = np.frombuffer( self.sock.recv(2048), dtype=np.uint16)
                #lg.debug(vhex(res))
                return res
            except timeout:
                lg.warning('socket timeout')
                return None
            
        except OSError as e:
            lg.warning(e)

    #-------------------------------------------------------
    def empty(self):
        """Empty the UDP buffer."""
        self.sock.settimeout(0.0)
        while True:
            try:
                self.sock.recv(2048)
            except:
                self.sock.settimeout(0.5)
                return

    #-------------------------------------------------------
    def close(self):
        self.sock.close()
        
#-------------------------------------------------------------------------------
class SocketThread(threading.Thread):

    #-------------------------------------------------------
    def __init__(self, name='Socket Thread' ):
        super().__init__()

        self.link_up = False
        self.chksock = Socket(HOST_IP, LB_PORT, DEVICE_IP)
    #-------------------------------------------------------
    def finish(self):
        lg.info('Socket Thread pending to finish')
        command_queue.put(None)

    #-------------------------------------------------------
    def run(self):
        while True:
            data = np.arange(10, dtype=np.uint16)
            res = self.chksock.processing(data)

            if not isinstance(res, np.ndarray):
                if self.link_up:
                    lg.info('link down')
                    self.link_up = False
                    self.chksock.socket_status_signal.emit(0)
            else:
                if not self.link_up:
                    lg.info('link up')
                    self.link_up = True
                    self.chksock.socket_status_signal.emit(1)

            time.sleep(1)

            if not command_queue.empty():
                item = command_queue.get()
                if item:
                    fun  = item[0]
                    args = item[1]
                    fun(*args)
                else:
                    break
            
        lg.info('udp socket thread::run exit')
            
#-------------------------------------------------------------------------------
    
