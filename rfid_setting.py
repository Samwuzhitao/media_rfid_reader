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

ser           = 0
input_count   = 0
LOGTIMEFORMAT = '%Y%m%d%H'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time


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
        self.conf_frame.sync_sn_update()

        self.com_frame  = tag_ui(self.config, self.config_file_name )

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