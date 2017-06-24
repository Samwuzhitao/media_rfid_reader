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
from HexDecode    import *
from ComMonitor   import *
from led          import *

ser           = 0
input_count   = 0
LOGTIMEFORMAT = '%Y%m%d%H'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time
CONF_FONT_SIZE = 16

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

class ComWork(QDialog):
    def __init__(self, parent=None):
        global ser
        super(ComWork, self).__init__(parent)
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
        self.setWindowTitle(u"滤网RFID生产")
        self.showMaximized()

        self.e_button   = QPushButton(u"退出")
        self.e_button.setFixedSize(120, 50)
        self.e_button.setFont(QFont("Roman times",25,QFont.Bold))
        e_layout = QHBoxLayout()
        e_layout.addWidget(self.e_button)

        self.dtq_id_label=QLabel(u"产线号  :")
        self.dtq_id_label.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.dtq_id_lineedit = QLineEdit(u"0")
        self.dtq_id_lineedit.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.time_label=QLabel(u"生产日期:")
        self.time_label.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.manufacturer_label=QLabel(u"生产厂家:")
        self.manufacturer_label.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.manufacturer_lineedit = QLineEdit(u'FF')
        self.manufacturer_lineedit.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.mesh_type_label=QLabel(u"滤网类型:")
        self.mesh_type_label.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.mesh_type_combo = QComboBox()
        self.mesh_type_combo.addItems([u'0x01:复合滤网\PM2.5滤网',u'0x02:甲醛滤网',
            u'0x03:塑料袋NFC标签',u'0x04:非法滤网',u'0xFF:没有标签'])
        self.mesh_type_combo.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.des_label=QLabel(u"序列号  :")
        self.des_label.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.des_lineedit = QLineEdit(u'FF FF FF FF')
        self.des_lineedit.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.time_lineedit = QLineEdit( time.strftime(
            '%Y-%m-%d',time.localtime(time.time())))
        self.time_lineedit.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))

        g_hbox = QGridLayout()
        g_hbox.addWidget(self.time_label           ,0,0)
        g_hbox.addWidget(self.time_lineedit        ,0,1)
        g_hbox.addWidget(self.dtq_id_label         ,0,2)
        g_hbox.addWidget(self.dtq_id_lineedit      ,0,3)
        g_hbox.addWidget(self.mesh_type_label      ,2,0)
        g_hbox.addWidget(self.mesh_type_combo      ,2,1)
        g_hbox.addWidget(self.manufacturer_label   ,2,2)
        g_hbox.addWidget(self.manufacturer_lineedit,2,3)
        # g_hbox.addItem(QSpacerItem(10,10,QSizePolicy.Expanding,QSizePolicy.Minimum),2,0,2,3)
        g_hbox.addWidget(self.des_label            ,1,0)
        g_hbox.addWidget(self.des_lineedit         ,1,1,1,3)

        conf_frame = QFrame()
        conf_frame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        conf_frame.setLayout(g_hbox)

        self.com1_lable = QLabel(u"标签1")
        self.com1_lable.setAlignment(Qt.AlignCenter)
        self.com1_lable.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.led1  = LED(60)
        self.com2_lable = QLabel(u"标签2")
        self.com2_lable.setAlignment(Qt.AlignCenter)
        self.com2_lable.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.led2  = LED(60)
        self.com3_lable = QLabel(u"标签3")
        self.com3_lable.setAlignment(Qt.AlignCenter)
        self.com3_lable.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.led3  = LED(60)
        self.com4_lable = QLabel(u"标签4")
        self.com4_lable.setAlignment(Qt.AlignCenter)
        self.com4_lable.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.led4  = LED(60)
        c_gbox = QGridLayout()

        c_gbox.addWidget(self.led1      ,0,0)
        c_gbox.addWidget(self.led2      ,0,1)
        c_gbox.addWidget(self.led3      ,0,2)
        c_gbox.addWidget(self.led4      ,0,3)
        c_gbox.addWidget(self.com1_lable,1,0)
        c_gbox.addWidget(self.com2_lable,1,1)
        c_gbox.addWidget(self.com3_lable,1,2)
        c_gbox.addWidget(self.com4_lable,1,3)

        # com_frame = QFrame()
        # com_frame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        # com_frame.setLayout(c_gbox)

        self.sw_label   = QLabel(u"滤网RFID标签授权")
        self.sw_label.setFont(QFont("Roman times",40,QFont.Bold))
        self.sw_label.setAlignment(Qt.AlignCenter)

        self.zkxl_label = QLabel(u"版权所有：深圳中科讯联科技有限公司")
        self.zkxl_label.setFont(QFont("Roman times",20,QFont.Bold))
        self.zkxl_label.setAlignment(Qt.AlignCenter)

        box = QVBoxLayout()
        box.addItem(QSpacerItem(60,60,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addWidget(self.sw_label)
        box.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addWidget(conf_frame)
        box.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addLayout(c_gbox)
        box.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addLayout(e_layout)
        box.addItem(QSpacerItem(30,30,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addWidget(self.zkxl_label)
        box.addItem(QSpacerItem(30,30,QSizePolicy.Expanding,QSizePolicy.Minimum))

        self.setLayout(box)

        self.config_data_sync()

        self.e_button.clicked.connect(self.clear_text)
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
        print "exit"
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
    def work_start(parent = None):
        comsetting_dialog = ComWork(parent)
        result = comsetting_dialog.exec_()

        return (comsetting_dialog.ComMonitor)

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = ComWork()
    datburner.show()
    app.exec_()

    if ser != 0:
        datburner.find_card_stop()
        datburner.setting_uart(0)



