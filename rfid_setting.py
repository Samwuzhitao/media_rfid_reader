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
import ConfigParser
from cmd_rev_decode import *
from com_monitor    import *
from led            import *
from sn_config      import *

ser           = 0
input_count   = 0
LOGTIMEFORMAT = '%Y%m%d%H'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time

class tag_data():
    def __init__(self):
        self.ser_list     = []
        self.ser_list_index = {}
        self.ports_dict   = {}
        self.ser_dict     = {}
        self.monitor_dict = {}
        self.led_dict     = {}

class tag_ui(QFrame):
    def __init__(self, config, file_name, parent=None):
        self.tag = tag_data()
        # get uart Config
        self.config = config
        self.config_file_name  = file_name
        # file_num = config.get('script', 'file_num')

        super(tag_ui, self).__init__(parent)
        self.com1_combo=QComboBox(self)
        self.uart_scan(self.com1_combo)
        self.com1_button = QPushButton(u"绑定标签1")
        self.led1  = LED(40)
        # self.tag.led_list.append(self.led1)
        self.com2_combo=QComboBox(self)
        self.uart_scan(self.com2_combo)
        self.com2_button = QPushButton(u"绑定标签2")
        self.led2  = LED(40)
        # self.tag.led_list.append(self.led2)
        self.com3_combo=QComboBox(self)
        self.uart_scan(self.com3_combo)
        self.com3_button = QPushButton(u"绑定标签3")
        self.led3  = LED(40)
        # self.tag.led_list.append(self.led3)
        self.com4_combo=QComboBox(self)
        self.uart_scan(self.com4_combo)
        self.com4_button = QPushButton(u"绑定标签4")
        self.led4  = LED(40)
        # self.tag.led_list.append(self.led4)
        c_gbox = QGridLayout()
        c_gbox.addWidget(self.led1       ,0,0)
        c_gbox.addWidget(self.led2       ,0,1)
        c_gbox.addWidget(self.led3       ,0,2)
        c_gbox.addWidget(self.led4       ,0,3)
        c_gbox.addWidget(self.com1_combo ,1,0)
        c_gbox.addWidget(self.com2_combo ,1,1)
        c_gbox.addWidget(self.com3_combo ,1,2)
        c_gbox.addWidget(self.com4_combo ,1,3)
        c_gbox.addWidget(self.com1_button,2,0)
        c_gbox.addWidget(self.com2_button,2,1)
        c_gbox.addWidget(self.com3_button,2,2)
        c_gbox.addWidget(self.com4_button,2,3)

        self.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.setLayout(c_gbox)

        self.com1_button.clicked.connect(self.band_start)
        self.com2_button.clicked.connect(self.band_start)
        self.com3_button.clicked.connect(self.band_start)
        self.com4_button.clicked.connect(self.band_start)

    def uart_scan(self,combo):
        for i in range(256):
            try:
                s = serial.Serial(i)
                combo.addItem(s.portstr)
                self.tag.ports_dict[s.portstr] = i
                s.close()
            except serial.SerialException:
                pass

    def setting_uart(self,ser_index,mode):
        global ser
        global input_count

        if ser_index == 1:
            serial_port = str(self.com1_combo.currentText())
            self.tag.led_dict[serial_port] = self.led1
            self.tag.ser_list_index[serial_port] = ser_index
        if ser_index == 2:
            serial_port = str(self.com2_combo.currentText())
            self.tag.led_dict[serial_port]  = self.led2
            self.tag.ser_list_index[serial_port] = ser_index
        if ser_index == 3:
            serial_port = str(self.com3_combo.currentText())
            self.tag.led_dict[serial_port]  = self.led3
            self.tag.ser_list_index[serial_port] = ser_index
        if ser_index == 4:
            serial_port = str(self.com4_combo.currentText())
            self.tag.led_dict[serial_port]  = self.led4
            self.tag.ser_list_index[serial_port] = ser_index
        try:
            ser = serial.Serial( self.tag.ports_dict[serial_port], 115200)
        except serial.SerialException:
            pass

        if mode == 1:
            if ser.isOpen() == True:
                if self.tag.monitor_dict.has_key(serial_port) == True:
                    # self.tag.monitor_dict[serial_port]
                    print "11111111"
                else:
                    self.tag.ser_list.append(serial_port)
                    self.tag.ser_dict[serial_port]     = ser
                    self.tag.monitor_dict[serial_port] = ComMonitor(ser)
                    self.connect(self.tag.monitor_dict[serial_port],
                        SIGNAL('r_cmd_message(QString,QString)'),
                        self.sync_rf_config_data)
                return serial_port

    def band_start(self):
        button = self.sender()
        button_str = button.text()

        if button_str == u"绑定标签1" or button_str == u"绑定标签2" or \
           button_str == u"绑定标签3" or button_str == u"绑定标签4":

            button_index = string.atoi( str(button_str[-1:]), 10 )
            serial_port = self.setting_uart(button_index,1)

            if self.tag.ser_dict[serial_port].isOpen() == True:
                button.setText(u"断开绑定标签%d" % button_index)
                print "标签%d绑定标签:%s" % ( button_index, serial_port )
                self.tag.monitor_dict[serial_port].start()
                send_cmd  =  "5A 02 0D 01 0E CA"
                send_cmd = str(send_cmd.replace(' ',''))
                send_cmd = send_cmd.decode("hex")
                self.tag.ser_dict[serial_port].write(send_cmd)

        if button_str == u"断开绑定标签1" or button_str == u"断开绑定标签2" or \
           button_str == u"断开绑定标签3" or button_str == u"断开绑定标签4":

            button_index = string.atoi( str(button_str[-1:]), 10 )
            try:
                serial_port  = self.tag.ser_list[button_index-1]
            except IndexError:
                return

            button.setText(u"绑定标签%d" % button_index)

            if self.tag.ser_dict[serial_port].isOpen() == True:
                print "断开标签%d绑定串口:%s" % ( button_index, serial_port )
                send_cmd  =  "5A 02 CC 01 CF CA"
                send_cmd = str(send_cmd.replace(' ',''))
                send_cmd = send_cmd.decode("hex")
                self.tag.ser_dict[serial_port].write(send_cmd)

    def sync_rf_config_data(self,port,data):
        port = str(port)
        # 端口连接指令
        if str(data) == "5A020D010ECA" or str(data) == "5A020D020DCA" or str(data) == "5A02CC01CFCA":
            if str(data) == "5A020D010ECA":
                self.tag.led_dict[port].set_color("green")
                self.config.set('serial', 'port%d' %  self.tag.ser_list_index[port], port )
            if str(data) == "5A020D020DCA":
                self.tag.led_dict[port].set_color("red")
                self.config.delete('serial', 'port%d' %  self.tag.ser_list_index[port], port )
            if str(data) == "5A02CC01CFCA":
                self.tag.led_dict[port].set_color("blue")
            self.config.write(open(self.config_file_name,"w"))


class ComSetting(QDialog):
    def __init__(self, parent=None):
        global ser
        super(ComSetting, self).__init__(parent)

        self.setWindowTitle(u"滤网RFID配置")
        self.clear_button = QPushButton(u"保存配置")
        self.clear_button.setFont(QFont("Roman times",15,QFont.Bold))
        self.clear_button.setFixedHeight(40)

        self.config = ConfigParser.ConfigParser()
        self.config_file_name = os.path.abspath("./") + '\\data\\' + '\\config\\' + 'config.inf'
        self.config.readfp(open(self.config_file_name, "rb"))

        self.conf_frame = sn_ui( None,0,self.config, self.config_file_name )
        self.com_frame  = tag_ui(self.config, self.config_file_name )
        self.conf_frame.sync_sn_update()

        box = QVBoxLayout()
        box.addWidget(self.com_frame)
        box.addWidget(self.conf_frame)
        box.addWidget(self.clear_button)
        self.setLayout(box)

        self.clear_button.clicked.connect(self.clear_text)


    def clear_text(self):
        self.conf_frame.config_data_sync()
        self.close()

    @staticmethod
    def get_com_monitor(parent = None):
        comsetting_dialog = ComSetting(parent)
        result = comsetting_dialog.exec_()

        return (comsetting_dialog.com_frame.tag.ser_list,
                comsetting_dialog.com_frame.tag.monitor_dict)

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = ComSetting()
    datburner.show()
    app.exec_()

    # if ser != 0:
        # datburner.find_card_stop()
        # datburner.setting_uart(0)



