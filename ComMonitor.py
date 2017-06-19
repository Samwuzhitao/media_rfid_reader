# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: Samwu
"""
import string
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

from HexDecode  import *

class ComMonitor(QThread):
    def __init__(self,com,parent=None):
        super(ComMonitor,self).__init__(parent)
        self.working  = True
        self.num      = 0
        self.com      = com
        # print self.com
        self.input_count      = 0
        self.decode_type_flag = 0
        self.hex_decode_show_style = 1
        self.down_load_image_flag  = 0
        self.image_path            = ''
        self.info_str = ''
        self.rev_machine   = HexDecode()
        self.ReviceFunSets = {
            0:self.uart_cmd_decode,
        }
        self.DecodeFunSets = {
            0:self.rev_machine.r_machine,
        }

    def __del__(self):
        self.working=False
        self.wait()

    def uart_cmd_decode(self,read_char):
        recv_str      = ""

        self.hex_revice.show_style = self.hex_decode_show_style
        str1 = self.DecodeFunSets[self.decode_type_flag](read_char)

        if str1 :
            recv_str =  str1

        return 0,recv_str

    def run(self):
        while self.working==True:
            if self.com.isOpen() == True:
                read_char = self.com.read(1)

                #print "status = %d char = %02X " % (down_load_image_flag, ord(read_char))
                next_flag,recv_str = self.ReviceFunSets[self.down_load_image_flag]( read_char )

                if recv_str :
                    if self.down_load_image_flag != 1:
                        self.emit(SIGNAL('protocol_message(QString, QString)'),self.com.portstr,recv_str)
                        #print 'protocol_message(QString)',
                    else:
                        self.emit(SIGNAL('download_image_info(QString, QString)'),self.com.portstr,recv_str )
                    #print "status = %d char = %s str = %s" % (self.down_load_image_flag, read_char, recv_str)
                self.down_load_image_flag = next_flag