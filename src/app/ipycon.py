

import os
import threading
import subprocess
import shlex

from logger import logger as lg


#-------------------------------------------------------------------------------
class TConsoleLaunchThread(threading.Thread):


    def __init__(self, connection_file, console, name='Jupyter Console Launch Thread' ):
        super().__init__()
        self.connection_file = connection_file
        self.console = console

        #self.logger = TLogger()

    def run(self):

        lg.info('waiting for start Jupyter kernel...')
        lg.warning('slon = [mamont] @kot, (slonick&). Kotick: {gray}, ^slon ~= $kot')
        lg.info('Connection file: ' + self.connection_file)
        #Logger.info('waiting for start Jupyter kernel...')
        
        while True:
            if os.path.exists(self.connection_file):
                break
            time.sleep(0.3)
            
        lg.info('Console type: ' + self.console)

        if self.console == 'shell':
            console = 'jupyter console --existing ' + self.connection_file
            cmd = 'terminator -T "IPython Console" --new-tab -e "' + console + '"'
        elif self.console == 'qt':
            cmd = 'jupyter qtconsole --existing ' + self.connection_file
        else:
            lg.warning('E: invalid console type: ' + self.console)
            #Logger.info('E: invalid console type: ' + self.console)
            return

        lg.debug(cmd)

       # Logger.info('launching Jupyter console...')
       # Logger.info(cmd)

        p = subprocess.Popen( shlex.split(cmd), universal_newlines = True,
                     stdin  = subprocess.PIPE,
                     stdout = subprocess.PIPE,
                     stderr = subprocess.PIPE )

       # Logger.info('Jupyter Console has launched')

#-------------------------------------------------------------------------------
def launch_jupyter_console(cfile, ctype):
    clthread = TConsoleLaunchThread(cfile, ctype)
    clthread.start()

#-------------------------------------------------------------------------------

