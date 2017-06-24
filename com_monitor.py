# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: Samwu
"""
import string
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

from cmd_rev_decode import *

class ComMonitor(QThread):
    def __init__(self,com,parent=None):
        super(ComMonitor,self).__init__(parent)
        self.working  = True
        self.com      = com
        self.rcmd     = HexDecode()
        self.scmd     = HexDecode()
        self.s_count  = 0

    def __del__(self):
        self.working=False
        self.wait()

    def run(self):
        while self.working==True:
            if self.com.isOpen() == True:
                read_char = self.com.read(1)
                recv_str  = self.rcmd.r_machine(read_char)

                if recv_str :
                    self.rcmd.clear()
                    self.emit(SIGNAL('r_cmd_message( QString)'),recv_str)
