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
from tag_config     import *

class ComSetting(QDialog):
    def __init__(self, parent=None):
        global ser
        super(ComSetting, self).__init__(parent)
        self.showMaximized()
        self.setWindowTitle(u"滤网RFID配置")

        self.clear_button = QPushButton(u"保存配置")
        self.clear_button.setFixedSize(240, 50)
        self.clear_button.setFont(QFont("Roman times",25,QFont.Bold))

        self.bind_button = QPushButton(u"搜索设备")
        self.bind_button.setFixedSize(240, 50)
        self.bind_button.setFont(QFont("Roman times",25,QFont.Bold))

        e_layout = QHBoxLayout()
        e_layout.addWidget(self.bind_button)
        e_layout.addWidget(self.clear_button)

        self.config = ConfigParser.ConfigParser()
        self.config_file_name = os.path.abspath("./") + '\\data\\' + '\\config\\' + 'config.inf'
        self.config.readfp(open(self.config_file_name, "rb"))

        self.conf_frame = sn_ui( 16,0,self.config, self.config_file_name )
        self.tag_frame  = tag_ui( self.config, self.config_file_name )

        self.sw_label   = QLabel(u"滤网RFID标签授权")
        self.sw_label.setFont(QFont("Roman times",40,QFont.Bold))
        self.sw_label.setAlignment(Qt.AlignCenter)
        self.zkxl_label = QLabel(u"版权所有：深圳中科讯联科技股份有限公司")
        self.zkxl_label.setFont(QFont("Roman times",20,QFont.Bold))
        self.zkxl_label.setAlignment(Qt.AlignCenter)

        box = QVBoxLayout()
        box.addItem(QSpacerItem(40,40,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addWidget(self.sw_label)
        box.addWidget(self.tag_frame)
        box.addWidget(self.conf_frame)
        box.addLayout(e_layout)
        box.addWidget(self.zkxl_label)
        box.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        self.setLayout(box)

        self.clear_button.clicked.connect(self.clear_text)
        self.bind_button.clicked.connect(self.auto_search_device)

    def auto_search_device(self):
        com1_str = self.tag_frame.uart_auto_connect(0)
        if com1_str:
            self.tag_frame.com1_lable.setText(u"标签1:%s" % com1_str)
        com2_str = self.tag_frame.uart_auto_connect(1)
        if com2_str:
            self.tag_frame.com2_lable.setText(u"标签2:%s" % com2_str)
        com3_str = self.tag_frame.uart_auto_connect(2)
        if com3_str:
            self.tag_frame.com3_lable.setText(u"标签3:%s" % com3_str)
        com4_str = self.tag_frame.uart_auto_connect(3)
        if com4_str:
            self.tag_frame.com4_lable.setText(u"标签4:%s" % com4_str)

    def clear_text(self):
        # self.conf_frame.config_data_sync()
        self.close()

    @staticmethod
    def get_com_monitor(parent = None):
        comsetting_dialog = ComSetting(parent)
        result = comsetting_dialog.exec_()
        comsetting_dialog.conf_frame.config_data_sync()
        if comsetting_dialog.config != None:
            # if comsetting_dialog.tag_frame.tag.ser_list[0]
            if len(comsetting_dialog.tag_frame.tag.ser_list) == 4:
                comsetting_dialog.config.set('serial', 'port1', comsetting_dialog.tag_frame.tag.ser_list[0])
                comsetting_dialog.config.set('serial', 'port2', comsetting_dialog.tag_frame.tag.ser_list[1])
                comsetting_dialog.config.set('serial', 'port3', comsetting_dialog.tag_frame.tag.ser_list[2])
                comsetting_dialog.config.set('serial', 'port4', comsetting_dialog.tag_frame.tag.ser_list[3])
                comsetting_dialog.config.write(open(comsetting_dialog.config_file_name,"w"))

            for item in comsetting_dialog.tag_frame.tag.ser_list:
                comsetting_dialog.tag_frame.tag.monitor_dict[item].com.close()
                comsetting_dialog.tag_frame.tag.monitor_dict[item].quit()

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = ComSetting()
    datburner.show()
    app.exec_()