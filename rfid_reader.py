# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: Samwu
"""
import serial
import string
import time
import os
import sys
import logging
import ConfigParser
from time import sleep
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from ctypes import *
from math import *

from ComSetting import *

class RFIDReader(QWidget):
    def __init__(self, parent=None):
        super(RFIDReader, self).__init__(parent)
        self.monitor_dict  = {}
        self.com_dict      = {}

        self.showMaximized()
        self.setWindowTitle(u'滤网RFID标签授权软件 V2.0')
        palette1 = QPalette()
        palette1.setColor(self.backgroundRole(), QColor(85,85,255))
        self.setPalette(palette1)
        self.sw_label   = QLabel(u"滤网RFID标签授权")
        self.sw_label.setFont(QFont("Roman times",40,QFont.Bold))
        self.sw_label.setAlignment(Qt.AlignCenter)
        self.m_button   = QPushButton(u"1.管理者操作  ")
        self.m_button.setFixedHeight(40)
        self.m_button.setStyleSheet(
            "QPushButton{border:1px solid rgb(85,85,255);background:rgb(85,85,255)}"
            "QPushButton:hover{border-color:lightgray;}")
        self.m_button.setFont(QFont("Roman times",25,QFont.Bold))
        self.p_button   = QPushButton(u"2.产线工人操作")
        self.p_button.setFixedHeight(40)
        self.p_button.setStyleSheet(
            "QPushButton{border:1px solid rgb(85,85,255);background:rgb(85,85,255)}"
            "QPushButton:hover{border-color:lightgray;}")
        self.p_button.setFont(QFont("Roman times",25,QFont.Bold))
        self.e_button   = QPushButton(u"退出")
        self.e_button.setFixedSize(200, 40)

        self.e_button.setFont(QFont("Roman times",15,QFont.Bold))
        self.zkxl_label = QLabel(u"版权所有：深圳中科讯联科技有限公司")
        self.zkxl_label.setFont(QFont("Roman times",20,QFont.Bold))
        self.zkxl_label.setAlignment(Qt.AlignCenter)

        e_layout = QHBoxLayout()
        e_layout.addWidget(self.e_button)

        c_hbox = QVBoxLayout()
        c_hbox.addStretch()
        c_hbox.addWidget(self.sw_label)
        c_hbox.addStretch()
        c_hbox.addWidget(self.m_button)
        c_hbox.addWidget(self.p_button)
        c_hbox.addStretch()
        c_hbox.addLayout(e_layout)
        c_hbox.addStretch()
        c_hbox.addWidget(self.zkxl_label)

        mylayout = QVBoxLayout()
        self.setLayout(c_hbox)

        self.e_button.clicked.connect(self.close)
        self.m_button.clicked.connect(self.open_new_session)

    def open_new_session(self):
        monitor = ComSetting.get_com_monitor()
        if monitor :
            # 创建监听线程
            self.monitor_dict[monitor.com.portstr] = monitor
            self.com_dict[monitor.com.portstr]     = monitor.com

            # self.connect(self.monitor_dict[monitor.com.portstr],
                         # SIGNAL('protocol_message(QString, QString)'),
                         # self.update_edit)

            self.monitor_dict[monitor.com.portstr].start()
            logging.info(u"启动串口监听线程!")
            # self.com_edit.append(u"启动串口 %s 监听线程!" % monitor.com.portstr )
        # else:
            # self.com_edit.append(u"Error:打开串口出错！")


if __name__=='__main__':
    app = QApplication(sys.argv)
    rfid = RFIDReader()
    rfid.show()
    app.exec_()

