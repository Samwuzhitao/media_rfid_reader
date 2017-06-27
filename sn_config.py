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

class sn_data():
    def __init__(self):
        self.date      = ""
        self.machine   = 0
        self.number    = 0
        self.mesh      = None
        self.factory   = None

    def get_sn(self):
        date_year = string.atoi(self.date[0:2],10)-17
        date_mon  = string.atoi(self.date[2:4],10)
        byte1_code = "%02X" % ((date_year << 4) | (date_mon & 0x0F))
        byte2_1_code = "%01X" % (string.atoi(self.machine,10) << 4)
        byte2_2_3_4  = "%05X" % self.number

        sn = byte1_code + byte2_1_code + byte2_2_3_4
        return sn

class sn_ui(QFrame):
    def __init__(self, font_size, read_mode, config=None, file_name=None, parent=None):
        self.sn = sn_data()
        self.config = config
        self.config_file_name  = file_name
        super(sn_ui, self).__init__(parent)
        self.line_label=QLabel(u"产线号  :")
        self.line_lineedit = QLineEdit(u"0")
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

        if read_mode == 1:
            self.line_lineedit.setReadOnly(True)
            self.manufacturer_lineedit.setReadOnly(True)
            self.des_lineedit.setReadOnly(True)
            self.time_lineedit.setReadOnly(True)

        if font_size != None:
            self.line_label.setFont(QFont(           "Roman times",font_size,QFont.Bold))
            self.line_lineedit.setFont(QFont(        "Roman times",font_size,QFont.Bold))
            self.time_label.setFont(QFont(           "Roman times",font_size,QFont.Bold))
            self.manufacturer_label.setFont(QFont(   "Roman times",font_size,QFont.Bold))
            self.manufacturer_lineedit.setFont(QFont("Roman times",font_size,QFont.Bold))
            self.mesh_type_label.setFont(QFont(      "Roman times",font_size,QFont.Bold))
            self.mesh_type_combo.setFont(QFont(      "Roman times",font_size,QFont.Bold))
            self.des_label.setFont(QFont(            "Roman times",font_size,QFont.Bold))
            self.des_lineedit.setFont(QFont(         "Roman times",font_size,QFont.Bold))
            self.time_lineedit.setFont(QFont(        "Roman times",font_size,QFont.Bold))

        g_hbox = QGridLayout()
        g_hbox.addWidget(self.time_label           ,0,0)
        g_hbox.addWidget(self.time_lineedit        ,0,1)
        g_hbox.addWidget(self.line_label           ,0,2)
        g_hbox.addWidget(self.line_lineedit        ,0,3)
        g_hbox.addWidget(self.des_label            ,1,0)
        g_hbox.addWidget(self.des_lineedit         ,1,1,1,3)
        g_hbox.addWidget(self.mesh_type_label      ,2,0)
        g_hbox.addWidget(self.mesh_type_combo      ,2,1)
        g_hbox.addWidget(self.manufacturer_label   ,2,2)
        g_hbox.addWidget(self.manufacturer_lineedit,2,3)

        self.sync_sn_str()
        self.des_lineedit.setText(self.sn.get_sn())

        self.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.setLayout(g_hbox)
        self.mesh_type_combo.currentIndexChanged.connect(self.config_data_sync)

    def sync_sn_update(self):
        self.sn.date    = self.config.get('SN', 'date'    )
        self.sn.machine = self.config.get('SN', 'machine' )
        self.sn.number  = string.atoi(self.config.get('SN', 'number'  ))
        self.sn.mesh    = self.config.get('SN', 'mesh'    )
        self.sn.sn      = self.config.get('SN', 'sn'      )
        self.sn.factory = self.config.get('SN', 'factory' )

        self.manufacturer_lineedit.setText(self.sn.factory)
        self.line_lineedit.setText(self.sn.machine)

        self.sync_sn_str()
        self.des_lineedit.setText(self.sn.get_sn())

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

        mac_str = str(self.line_lineedit.text())
        self.sn.machine = mac_str

    def config_data_sync(self):
        self.sync_sn_str()
        self.des_lineedit.setText(self.sn.get_sn())
        if self.config != None:
            self.config.set('SN', 'date'   , self.sn.date    )
            self.config.set('SN', 'machine', self.sn.machine )
            self.config.set('SN', 'number' , self.sn.number  )
            self.config.set('SN', 'mesh'   , self.sn.mesh    )
            self.config.set('SN', 'factory', self.sn.factory )
            self.config.set('SN', 'sn'     , self.sn.get_sn())

            self.config.write(open(self.config_file_name,"w"))

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = sn_ui(16,0)
    datburner.show()
    app.exec_()




