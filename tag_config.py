# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import serial
import string
import time
import os
import sys
import logging
import json
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from com_monitor  import *
from led          import *
import ConfigParser

class tag_data():
    def __init__(self):
        self.ser_list     = []
        self.monitor_dict = {}
        self.led_list     = []

class tag_ui(QFrame):
    def __init__(self, config, file_name, parent=None):
        self.tag = tag_data()
        self.config = config
        self.config_file_name  = file_name

        super(tag_ui, self).__init__(parent)
        self.com1_lable = QLabel(u"标签1")
        self.com1_lable.setFont(QFont("Roman times",16,QFont.Bold))
        self.com1_lable.setAlignment(Qt.AlignCenter)
        self.led1  = LED(60)
        self.tag.led_list.append(self.led1)

        self.com2_lable = QLabel(u"标签2")
        self.com2_lable.setFont(QFont("Roman times",16,QFont.Bold))
        self.com2_lable.setAlignment(Qt.AlignCenter)
        self.led2  = LED(60)
        self.tag.led_list.append(self.led2)

        self.com3_lable = QLabel(u"标签3")
        self.com3_lable.setFont(QFont("Roman times",16,QFont.Bold))
        self.com3_lable.setAlignment(Qt.AlignCenter)
        self.led3  = LED(60)
        self.tag.led_list.append(self.led3)

        self.com4_lable = QLabel(u"标签4")
        self.com4_lable.setFont(QFont("Roman times",16,QFont.Bold))
        self.com4_lable.setAlignment(Qt.AlignCenter)
        self.led4  = LED(60)
        self.tag.led_list.append(self.led4)

        c_gbox = QGridLayout()
        c_gbox.addWidget(self.led1       ,0,0)
        c_gbox.addWidget(self.led2       ,0,1)
        c_gbox.addWidget(self.led3       ,0,2)
        c_gbox.addWidget(self.led4       ,0,3)
        c_gbox.addWidget(self.com1_lable ,1,0)
        c_gbox.addWidget(self.com2_lable ,1,1)
        c_gbox.addWidget(self.com3_lable ,1,2)
        c_gbox.addWidget(self.com4_lable ,1,3)

        self.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.setLayout(c_gbox)

    def uart_auto_connect(self,tag_index):
        connect_cmd =  "5A 02 0D 01 0E CA"
        connect_cmd = str(connect_cmd.replace(' ',''))
        connect_cmd = connect_cmd.decode("hex")
        hex_decode  = HexDecode()
        ser         = None
        ser_list    = []
        ports_dict  = {}

        # 扫描串口
        for i in range(256):
            try:
                s = serial.Serial(i)
                ports_dict[s.portstr] = i
                ser_list.append(s.portstr)
                s.close()
            except serial.SerialException:
                pass
        # print ser_list
        # 发送链接指令
        for item in ser_list:
            try:
                ser = serial.Serial( ports_dict[item], 115200, timeout = 0.5)
            except serial.SerialException:
                pass
            if ser:
                if ser.isOpen() == True:
                    ser.write(connect_cmd)
                    cmd_result = ser.read(6)
                    for i in cmd_result:
                        cmd_str = hex_decode.r_machine(i)
                        if cmd_str:
                            if cmd_str[4:8] == '0D01': # 打开串口OK
                                self.tag.led_list[tag_index].set_color("blue")
                                self.tag.monitor_dict[item] = ComMonitor(ser)
                                self.tag.ser_list.append(item)
                                print "标签%d 绑定串口%s" % (tag_index,item)
                                return item
                            if cmd_str[4:8] == '0D02': # 打开串口失败
                                self.tag.led_list[tag_index].set_color("gray")
                            return None

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = tag_ui(None,None)
    datburner.show()
    app.exec_()




