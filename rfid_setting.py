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

from cmd_rev_decode import *
from com_monitor    import *
from led            import *

ser           = 0
input_count   = 0
LOGTIMEFORMAT = '%Y%m%d%H'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time

class SNConfig():
    def __init__(self):
        self.date    = ""
        self.machine = ""
        self.number  = 0

    def get_sn(self):
        date_year = string.atoi(self.date[0:2],10)-17
        date_mon  = string.atoi(self.date[2:4],10)
        byte1_code = "%02X" % ((date_year << 4) | (date_mon & 0x0F))
        byte2_1_code = "%01X" % (string.atoi(self.machine,10) << 4)
        byte2_2_3_4  = "%05X" % self.number

        sn = byte1_code + byte2_1_code + byte2_2_3_4
        return sn

class ComSetting(QDialog):
    def __init__(self, parent=None):
        global ser
        super(ComSetting, self).__init__(parent)
        input_count     = 0
        self.port1_dict = {}
        self.port2_dict = {}
        self.port3_dict = {}
        self.port4_dict = {}
        self.ser        = None
        self.ComMonitor = None
        self.dtq_id     = ''
        self.r_cmd      = HexDecode()
        self.s_cmd      = HexDecode()
        self.sn         = SNConfig()
        self.s_cmd.init()
        self.setWindowTitle(u"滤网RFID配置")

        self.clear_button = QPushButton(u"保存配置")
        self.clear_button.setFont(QFont("Roman times",15,QFont.Bold))
        self.clear_button.setFixedHeight(40)

        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.clear_button)

        self.dtq_id_label=QLabel(u"产线号  :")
        self.dtq_id_lineedit = QLineEdit(u"0")
        self.time_label=QLabel(u"生产日期:")
        self.manufacturer_label=QLabel(u"生产厂家:")
        self.manufacturer_lineedit = QLineEdit(u'FF')
        self.mesh_type_label=QLabel(u"滤网类型:")
        self.mesh_type_combo = QComboBox()
        self.mesh_type_combo.addItems([u'0x01:复合滤网\PM2.5滤网',u'0x02:甲醛滤网',
            u'0x03:塑料袋NFC标签',u'0x04:非法滤网',u'0xFF:没有标签'])
        self.des_label=QLabel(u"序列号  :")
        self.des_lineedit = QLineEdit(u'FF FF FF FF')
        self.time_lineedit = QLineEdit( time.strftime(
            '%Y-%m-%d',time.localtime(time.time())))

        g_hbox = QGridLayout()
        # g_hbox.setSpacing(10)
        g_hbox.addWidget(self.time_label           ,0,0)
        g_hbox.addWidget(self.time_lineedit        ,0,1)
        g_hbox.addWidget(self.dtq_id_label         ,0,2)
        g_hbox.addWidget(self.dtq_id_lineedit      ,0,3)
        g_hbox.addWidget(self.des_label            ,1,0)
        g_hbox.addWidget(self.des_lineedit         ,1,1,1,3)
        g_hbox.addWidget(self.mesh_type_label      ,2,0)
        g_hbox.addWidget(self.mesh_type_combo      ,2,1)
        g_hbox.addWidget(self.manufacturer_label   ,2,2)
        g_hbox.addWidget(self.manufacturer_lineedit,2,3)

        conf_frame = QFrame()
        conf_frame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        conf_frame.setLayout(g_hbox)

        self.com1_combo=QComboBox(self)
        self.uart_scan(self.port1_dict,self.com1_combo)
        self.com1_button = QPushButton(u"绑定串口1")
        self.led1  = LED(40)
        self.com2_combo=QComboBox(self)
        self.uart_scan(self.port2_dict,self.com2_combo)
        self.com2_button = QPushButton(u"绑定串口2")
        self.led2  = LED(40)
        self.com3_combo=QComboBox(self)
        self.uart_scan(self.port3_dict,self.com3_combo)
        self.com3_button = QPushButton(u"绑定串口3")
        self.led3  = LED(40)
        self.com4_combo=QComboBox(self)
        self.uart_scan(self.port4_dict,self.com4_combo)
        self.com4_button = QPushButton(u"绑定串口4")
        self.led4  = LED(40)
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

        com_frame = QFrame()
        com_frame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        com_frame.setLayout(c_gbox)


        box = QVBoxLayout()
        box.addWidget(com_frame)
        box.addWidget(conf_frame)
        box.addLayout(c_hbox)
        self.setLayout(box)
        self.config_data_sync()

        self.clear_button.clicked.connect(self.clear_text)
        # self.start_button.clicked.connect(self.band_start)
        self.mesh_type_combo.currentIndexChanged.connect(self.config_data_sync)
        # self.com_combo.currentIndexChanged.connect(self.change_uart)

    def sync_sn_str(self):
        data_str = ''
        mesh_str = unicode(self.mesh_type_combo.currentText())
        if mesh_str == u'0x01:复合滤网\PM2.5滤网':
            self.sn.mesh = '01'
        if mesh_str == u'0x02:甲醛滤网':
            self.sn.mesh = '02'
        if mesh_str == u'0x03:塑料袋NFC标签':
            self.sn.mesh = '03'
        if mesh_str == u'0x04:非法滤网':
            self.sn.mesh = '04'
        if mesh_str == u'0xFF:没有标签':
            self.sn.mesh = 'FF'

        fac_str = str(self.manufacturer_lineedit.text())
        fac_str = fac_str.replace('-','')
        fac_str = fac_str.replace(' ','')
        self.sn.factory = fac_str

        time_str = str(self.time_lineedit.text())
        time_str = time_str[2:]
        time_str = time_str.replace('-','')
        time_str = time_str.replace(' ','')
        self.sn.date = time_str

        mac_str = str(self.dtq_id_lineedit.text())
        self.sn.machine = mac_str

    def config_data_sync(self):
        self.s_cmd.init()
        self.sync_sn_str()
        self.des_lineedit.setText(self.sn.get_sn())

    def uart_scan(self,dict,combo):
        for i in range(256):

            try:
                s = serial.Serial(i)
                if dict.has_key(s.portstr) == False:
                    combo.addItem(s.portstr)
                    dict[s.portstr] = i
                s.close()
            except serial.SerialException:
                pass

    def clear_text(self):
        # self.log_browser.clear()
        print "clear"
        self.close()

    def uart_update_text(self,data):
        global input_count
        print data
        logging.debug( data )
        cmd = str(data).decode("hex")
        for i in cmd:
            self.r_cmd.r_machine(i)
        show_str = u"R[%d]：%s" % (input_count,self.r_cmd.get_str(1))
        self.log_browser.append( show_str )

        if self.r_cmd.cmd_str == '0D':
            if self.r_cmd.op_str == '01':
                # self.log_browser.append(u"<font color=black>打开串口!</font>" )
                self.start_button.setText(u"关闭串口")
            if self.r_cmd.op_str == '00':
                # self.log_browser.append(u"<font color=black>关闭串口!</font>" )
                self.start_button.setText(u"打开串口")
                self.setting_uart(0)
        if self.r_cmd.cmd_str == '0B':
            if self.r_cmd.op_str == '01':
                # self.log_browser.append(u"<font color=black>设置失败</font>")
                logging.debug( u"设置失败" )
            if self.r_cmd.op_str == '00':
                # self.log_browser.append( u"<font color=black>设置成功</font>" )
                logging.debug( u"设置成功" )
        if self.r_cmd.cmd_str == '0A':
            if self.r_cmd.op_str == '00':
                # self.log_browser.append(u"<font color=black>读回UID : [%s]</font>" % self.r_cmd.data)
                logging.debug( u"读回UID : [%s]" % self.r_cmd.data )
            if self.r_cmd.op_str == '01':
                # self.log_browser.append(u"<font color=black>读回DES : %s</font>" % self.r_cmd.data)
                logging.debug( u"读回DES : %s" % self.r_cmd.data )
            if self.r_cmd.op_str == '02':
                # self.log_browser.append(u"<font color=black>读回TAG_DATA : %s</font>" % self.r_cmd.data)
                logging.debug( u"读回TAG_DATA : %s" % self.r_cmd.data )

        self.r_cmd.clear()

    def change_uart(self):
        global input_count
        global ser
        self.uart_scan(self.ports_dict)
        if ser != 0:
            input_count = 0
            ser.close()

    def setting_uart(self,mode):
        global ser
        global input_count

        serial_port = str(self.com_combo.currentText())

        try:
            ser = serial.Serial( self.ports_dict[serial_port], 115200)
        except serial.SerialException:
            pass

        if mode == 1:
            if ser.isOpen() == True:
                self.ComMonitor = ComMonitor(ser)
                input_count = input_count + 1
                self.ser    = ser
        else:
            if input_count > 0:

                input_count = 0
                ser.close()

    def band_start(self):
        global ser
        global input_count

        button = self.sender()
        button_str = button.text()

        if button_str == u"打开串口":
            self.setting_uart(1)
            if ser.isOpen() == True:
                input_count = input_count + 1
                send_cmd  =  "5A 02 0D 01 0E CA"
                log_str   = u"S[%d]：%s" % (input_count,send_cmd)
                # self.log_browser.append( log_str )
                logging.debug( log_str )
                send_cmd = str(send_cmd.replace(' ',''))
                print send_cmd
                send_cmd = send_cmd.decode("hex")
                ser.write(send_cmd)

        if button_str == u"关闭串口":
            send_cmd  =  "5A 02 0D 00 0F CA"
            log_str   = u"S[%d]：%s" % (input_count,send_cmd)
            # self.log_browser.append( log_str )
            logging.debug( log_str )
            send_cmd = str(send_cmd.replace(' ',''))
            send_cmd = send_cmd.decode("hex")
            ser.write(send_cmd)

    @staticmethod
    def get_com_monitor(parent = None):
        comsetting_dialog = ComSetting(parent)
        result = comsetting_dialog.exec_()

        return (comsetting_dialog.ComMonitor)

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = ComSetting()
    datburner.show()
    app.exec_()

    if ser != 0:
        datburner.find_card_stop()
        datburner.setting_uart(0)



