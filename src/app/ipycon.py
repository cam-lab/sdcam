#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: Jupyter console launch stuff
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
import threading
import subprocess
import shlex

from logger import logger as lg

#-------------------------------------------------------------------------------
class TConsoleLaunchThread(threading.Thread):

    def __init__(self, connection_file, settings, console, name='Jupyter Console Launch Thread' ):
        super().__init__()
        self.connection_file = connection_file.replace('\\', '/')
        self.settings = settings
        self.console  = console

    def run(self):

        lg.info('waiting for start Jupyter kernel...')
        lg.debug('Connection file: ' + self.connection_file)
        
        while True:
            if os.path.exists(self.connection_file):
                break
            time.sleep(0.3)
            
        lg.info('Console type: ' + self.console)

        if self.console == 'shell':
            con = self.settings['IPycon']
            geometry = con['Width'] + 'x' + con['Height'] + '+' + con['OrgX'] + '+' + con['OrgY']
            console = 'jupyter console --existing ' + self.connection_file
            cmd  = 'gnome-terminal -t IPython Console --geometry ' + geometry
            cmd += ' -- bash -c "' + console + '"'

        elif self.console == 'qt':
            con = self.settings['Qtcon']
            cmd = 'jupyter qtconsole --existing ' + self.connection_file
            cmd += ' --ConsoleWidget.font_family="'   + con['FontName'] + '"'
            cmd += ' --ConsoleWidget.font_size='      + con['FontSize']
            cmd += ' --ConsoleWidget.console_width='  + con['Width']
            cmd += ' --ConsoleWidget.console_height=' + con['Height']
            cmd += ' --ConsoleWidget.gui_completion_height=50'
            cmd += ' --ConsoleWidget.kind=rich'
            #cmd += ' --matplotlib inline'
        else:
            lg.warning('E: invalid console type: ' + self.console)
            return

        lg.debug(cmd)

        p = subprocess.Popen( shlex.split(cmd), universal_newlines = True,
                     stdin  = subprocess.PIPE,
                     stdout = subprocess.PIPE,
                     stderr = subprocess.PIPE )

        lg.info('Jupyter Console has launched')

#-------------------------------------------------------------------------------
def launch_jupyter_console(cfile, settings, ctype):
    clthread = TConsoleLaunchThread(cfile, settings, ctype)
    clthread.start()

#-------------------------------------------------------------------------------

