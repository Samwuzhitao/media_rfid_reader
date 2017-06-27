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
CONF_FONT_SIZE = 16

class ComWork(QDialog):
    def __init__(self,ser_list,monitor_dict,parent=None):
        global ser
        super(ComWork, self).__init__(parent)

        self.config = ConfigParser.ConfigParser()
        self.config_file_name = os.path.abspath("./") + '\\data\\' + '\\config\\' + 'config.inf'
        self.config.readfp(open(self.config_file_name, "rb"))

        input_count     = 0
        self.ser_list     = ser_list
        self.monitor_dict = monitor_dict
        self.port1_dict = {}
        self.port2_dict = {}
        self.port3_dict = {}
        self.port4_dict = {}
        self.ser        = None
        self.ComMonitor = None
        self.dtq_id     = ''
        self.r_cmd      = HexDecode()
        self.s_cmd      = HexDecode()
        # self.conf_frame.sn         = SNConfig()
        self.s_cmd.init()
        self.setWindowTitle(u"滤网RFID生产")
        self.showMaximized()

        self.e_button   = QPushButton(u"退出")
        self.e_button.setFixedSize(120, 50)
        self.e_button.setFont(QFont("Roman times",25,QFont.Bold))
        e_layout = QHBoxLayout()
        e_layout.addWidget(self.e_button)


        self.config = ConfigParser.ConfigParser()
        self.config_file_name = os.path.abspath("./") + '\\data\\' + '\\config\\' + 'config.inf'
        self.config.readfp(open(self.config_file_name, "rb"))

        self.conf_frame = sn_ui( 16,1,self.config, self.config_file_name )

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
        box.addWidget(self.conf_frame)
        box.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addLayout(c_gbox)
        box.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addLayout(e_layout)
        box.addItem(QSpacerItem(30,30,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addWidget(self.zkxl_label)
        box.addItem(QSpacerItem(30,30,QSizePolicy.Expanding,QSizePolicy.Minimum))

        self.setLayout(box)

        self.config_data_update()
        self.led_status_sync()

        self.e_button.clicked.connect(self.clear_text)
        self.conf_frame.mesh_type_combo.currentIndexChanged.connect(self.sync_mesh_data)

    def sync_mesh_data(self):
        self.mesh_type_combo.setCurrentIndex(string.atoi(self.conf_frame.sn.mesh)-1)

        self.sync_sn_str()
        self.des_lineedit.setText(self.conf_frame.sn.get_sn())

    def sync_sn_str(self):
        data_str = ''
        mesh_str = unicode(self.conf_frame.mesh_type_combo.currentText())
        if mesh_str == u'0x01:复合滤网\PM2.5滤网':
            self.conf_frame.sn.mesh = '01'
        if mesh_str == u'0x02:甲醛滤网':
            self.conf_frame.sn.mesh = '02'
        if mesh_str == u'0x03:塑料袋NFC标签':
            self.conf_frame.sn.mesh = '03'
        if mesh_str == u'0x04:非法滤网':
            self.conf_frame.sn.mesh = '04'
        if mesh_str == u'0xFF:没有标签':
            self.conf_frame.sn.mesh = 'FF'

        fac_str = str(self.conf_frame.manufacturer_lineedit.text())
        fac_str = fac_str.replace('-','')
        fac_str = fac_str.replace(' ','')
        self.conf_frame.sn.factory = fac_str

        time_str = str(self.conf_frame.time_lineedit.text())
        time_str = time_str[2:]
        time_str = time_str.replace('-','')
        time_str = time_str.replace(' ','')
        self.conf_frame.sn.date = time_str

        mac_str = str(self.conf_frame.line_lineedit.text())
        self.conf_frame.sn.machine = mac_str

    def led_status_sync(self):
        index = 0
        for item in self.ser_list:
            index = index + 1
            if self.monitor_dict[item].com.isOpen() == True:
                if index == 1:
                    self.led1.set_color("green")
                if index == 2:
                    self.led2.set_color("green")
                if index == 3:
                    self.led3.set_color("green")
                if index == 4:
                    self.led4.set_color("green")

    def config_data_update(self):
        self.conf_frame.sn.machine = self.config.get('SN', 'machine' )
        self.conf_frame.sn.number  = string.atoi(self.config.get('SN', 'number'  ))
        self.conf_frame.sn.mesh    = self.config.get('SN', 'mesh'    )
        self.conf_frame.sn.factory = self.config.get('SN', 'factory' )
        self.conf_frame.manufacturer_lineedit.setText(self.conf_frame.sn.factory)
        self.conf_frame.line_lineedit.setText(self.conf_frame.sn.machine)
        self.conf_frame.mesh_type_combo.setCurrentIndex(string.atoi(self.conf_frame.sn.mesh)-1)

        self.sync_sn_str()
        self.conf_frame.des_lineedit.setText(self.conf_frame.sn.get_sn())

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

    @staticmethod
    def work_start(ser_list,monitor_dict,parent = None):
        comsetting_dialog = ComWork(ser_list,monitor_dict,parent)
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



