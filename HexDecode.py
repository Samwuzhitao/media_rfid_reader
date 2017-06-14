
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import string

R_STATUS_HEADER = 0
R_STATUS_LEN    = 1
R_STATUS_CMD    = 2
R_STATUS_TYPE   = 3
R_STATUS_DTAT   = 4
R_STATUS_CRC    = 5
R_STATUS_END    = 6

class Cmd():
    def __init__(self):
        self.status  = 0
        self.header  = ""
        self.len     = 0
        self.len_str = ""
        self.cmd_type= ""
        self.op_type = ""
        self.data    = ""
        self.data_c  = 0
        self.r_crc   = ""
        self.end     = ""
        self.c_crc   = 0
        self.cmd_str = ""
        self.cmd_m   = {
            R_STATUS_HEADER : self.r_header,
            R_STATUS_LEN    : self.r_len,
            R_STATUS_CMD    : self.r_cmd,
            R_STATUS_TYPE   : self.r_type,
            R_STATUS_DTAT   : self.r_data,
            R_STATUS_CRC    : self.r_crc,
            R_STATUS_END    : self.r_end,
        }

    def clrar(self):
        self.status  = 0
        self.header  = ""
        self.len     = ""
        self.cmd_type= ""
        self.op_type = ""
        self.data    = ""
        self.r_crc   = ""
        self.end     = ""
        self.c_crc   = ""
        self.cmd_str = ""

    def r_header(self,x):
        if x == "5A":
            self.header =  x
            self.status = R_STATUS_LEN

    def r_len(self,x):
        self.c_crc  = self.c_crc ^ ord(x)
        self.status = R_STATUS_CMD
        self.len_str= x
        self.len    = ord(x)

    def r_cmd(self,x):
        self.c_crc  = self.c_crc ^ ord(x)
        self.status = R_STATUS_TYPE
        self.cmd_type = x

    def r_type(self,x):
        self.c_crc  = self.c_crc ^ ord(x)
        self.status = R_STATUS_DTAT
        self.op_type = x

    def r_data(self,x):
        self.c_crc  = self.c_crc ^ ord(x)
        self.data_c = data_c + 1
        self.data = self.data + x
        if self.data_c == (self.len-2):
            self.status = R_STATUS_CRC

    def r_crc(self,x):
        if self.c_crc  == ord(x):
            self.status = R_STATUS_END
            self.r_crc = x
        else:
            self.clear()

    def r_end(self,x):
        if x != "CA":
            self.clear()
        else:
            str = self.get_str()
            return str

    def get_str():
        str = self.header + self.len_str + self.type + \
              self.data + self.r_crc + self.end
        return str

class HexDecode():
    def __init__(self):
        self.cmd         = Cmd()
        self.cmd_str     = ""

    def r_machine(self,x):
        char = "%02X" % ord(x)
        print char
        self.cmd_str = self.cmd.cmd_m[self.cmd.status](char)
        if self.cmd_str:
            return self.cmd_str
        else:
            return ""

    
