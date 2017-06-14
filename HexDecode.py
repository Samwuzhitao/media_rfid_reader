
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
        self.cmd_str = ""
        self.op_str  = ""
        self.data    = ""
        self.data_c  = 0
        self.crc     = 0
        self.crc_str = ""
        self.end     = ""
        self.cmd_m   = {
            R_STATUS_HEADER : self.r_header ,
            R_STATUS_LEN    : self.r_len    ,
            R_STATUS_CMD    : self.r_cmd    ,
            R_STATUS_TYPE   : self.r_type   ,
            R_STATUS_DTAT   : self.r_data   ,
            R_STATUS_CRC    : self.r_crc_fun,
            R_STATUS_END    : self.r_end    
        }

    def clear(self):
        self.status  = 0
        self.header  = ""
        self.len     = 0
        self.len_str = ""
        self.cmd_str = ""
        self.op_str  = ""
        self.data    = ""
        self.data_c  = 0
        self.crc     = 0
        self.crc_str = ""
        self.end     = ""

    def r_header(self,x):
        if x == "5A":
            self.header =  x
            self.status = R_STATUS_LEN

    def r_len(self,x):
        self.crc  = self.crc ^ string.atoi(x, 16)
        self.status = R_STATUS_CMD
        self.len_str= x
        self.len    = string.atoi(x, 16)

    def r_cmd(self,x):
        self.crc  = self.crc ^ string.atoi(x, 16)
        self.status = R_STATUS_TYPE
        self.cmd_str = x

    def r_type(self,x):
        self.crc  = self.crc ^ string.atoi(x, 16)
        self.status = R_STATUS_DTAT
        self.op_str = x

    def r_data(self,x):
        self.crc  = self.crc ^ string.atoi(x, 16)
        self.data_c = self.data_c + 1
        self.data = self.data + x
        if self.data_c == (self.len-2):
            self.status = R_STATUS_CRC

    def r_crc_fun(self,x):
        self.r_crc = x 
        # print "c_crc = %02X r_crc = %s" % (self.crc,x)
        if self.crc == string.atoi(x, 16):
            self.status = R_STATUS_END
        else:
            self.clear()

    def r_end(self,x):
        self.end = x
        if x != "CA":
            self.clear()
        else:
            cmd_str = self.header + self.len_str + self.cmd_str + \
                      self.op_str + self.data + self.r_crc + self.end
            self.format_print()
            return cmd_str

    def format_print(self):
        print "header = %s" % self.header
        print "len    = %s" % self.len_str
        print "cmd    = %s" % self.cmd_str
        print "type   = %s" % self.op_str
        print "data   = %s" % self.data
        print "crc    = %s" % self.r_crc      
        print "end    = %s" % self.end   
        self.clear()
 
class HexDecode():
    def __init__(self):
        self.cmd         = Cmd()
        self.cmd_str     = ""

    def r_machine(self,x):
        char = "%02X" % ord(x)
        # print "status = %d, char = %s" % (self.cmd.status, char ) 
        self.cmd_str = self.cmd.cmd_m[self.cmd.status](char)
        if self.cmd_str:
            return self.cmd_str
        else:
            return ""

if __name__=='__main__':
    cmd_str = "5A 0B 0B 03 11 22 33 44 07 06 14 00 01 53 CA"
    hex_decode = HexDecode()
    print u"测试指令：%s" % cmd_str
    cmd_str = cmd_str.replace(' ','')
    cmd_str = cmd_str.decode("hex")
    for i in cmd_str:
        hex_decode.r_machine(i)