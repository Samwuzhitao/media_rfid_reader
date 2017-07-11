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
        self.date      = "1706"
        self.machine   = "01"
        self.number    = 0
        self.mesh      = "01"
        self.factory   = "01"
        self.ccm       = "01"
        self.excel_item= 1

    def get_sn(self):
        date_year = string.atoi(self.date[0:2],10)-17
        date_mon  = string.atoi(self.date[2:4],10)
        byte1_code = "%02X" % ((date_year << 4) | (date_mon & 0x0F))
        byte2_1_code = "%01X" % (string.atoi(self.machine,10)%10)
        byte2_2_3_4  = "%05X" % self.number

        sn = byte1_code + byte2_1_code + byte2_2_3_4
        return sn

    def get_tag(self):
        sn = self.get_sn()
        tag = sn + self.date + self.factory + self.mesh + "00000000"

        return tag

    def get_tag_cmd(self):
        crc_data = '0D' + self.get_tag()
        crc_len = len( crc_data )
        crc      = 0
        i = 0
        for item in crc_data:
            if i <= crc_len-2:
                crc  = crc ^ string.atoi(crc_data[i:i+2], 16)
                # print "c_crc = %02X crc_in = %s" % (self.crc,crc_data[i:i+2])
            i = i + 2
        crc_str = "%02X" % crc
        tag_cmd = '5A' + crc_data + crc_str + 'CA'

        return tag_cmd

class sn_ui(QFrame):
    def __init__(self, font_size, read_mode, config=None, file_name=None, parent=None):
        self.sn = sn_data()
        self.mode = read_mode
        self.config = config
        self.config_file_name  = file_name
        super(sn_ui, self).__init__(parent)
        self.line_label=QLabel(u"产线号  :")
        # self.line_lineedit = QLineEdit(u"01")
        self.line_type_combo = QComboBox()
        self.line_type_combo.addItems([u'01',u'02',u'03',u'04',u'05',u'06',u'07',u'08',u'09'])

        self.time_label=QLabel(u"生产日期:")
        self.manufacturer_label=QLabel(u"生产厂家:")
        self.manufacturer_lineedit = QLineEdit(u'01')
        self.mesh_type_label=QLabel(u"滤网类型:")
        self.mesh_type_combo = QComboBox()
        self.mesh_type_combo.addItems([u'0x01:复合滤网\PM2.5滤网',u'0x02:甲醛滤网',u'0x03:塑料袋NFC标签'])
        self.des_label=QLabel(u"序列号  :")
        self.des_lineedit = QLineEdit(u'')
        self.time_lineedit = QLineEdit( time.strftime(
            '%Y-%m-%d',time.localtime(time.time())))
        self.des_lineedit.setReadOnly(True)

        if self.mode == 1:
            self.manufacturer_lineedit.setReadOnly(True)
            self.time_lineedit.setReadOnly(True)

        if font_size != None:
            self.line_label.setFont(QFont(           "Roman times",font_size,QFont.Bold))
            self.line_type_combo.setFont(QFont(      "Roman times",font_size,QFont.Bold))
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
        g_hbox.addWidget(self.line_type_combo      ,0,3)
        g_hbox.addWidget(self.mesh_type_label      ,2,0)
        g_hbox.addWidget(self.mesh_type_combo      ,2,1)
        g_hbox.addWidget(self.manufacturer_label   ,2,2)
        g_hbox.addWidget(self.manufacturer_lineedit,2,3)

        d_hbox = QHBoxLayout()
        d_hbox.addWidget(self.des_label   )
        d_hbox.addWidget(self.des_lineedit)

        c_hbox = QVBoxLayout()
        c_hbox.addLayout(g_hbox)
        c_hbox.addLayout(d_hbox)

        self.sync_sn_update()

        self.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.setLayout(c_hbox)

        self.line_type_combo.currentIndexChanged.connect(self.line_change_sync)
        self.mesh_type_combo.currentIndexChanged.connect(self.mesh_change_sync)

    def sync_sn_update(self):
        self.sn.machine = self.config.get('SN', 'machine' )
        self.line_type_combo.setCurrentIndex(string.atoi(self.sn.machine)-1)
        line_index = string.atoi(str(self.line_type_combo.currentText()),10)

        if self.sn.machine != '':
            self.sn.sn      = self.config.get('SN', 'sn%d' % line_index )
            self.sn.number  = string.atoi(self.sn.sn[3:],16)
            self.sn.mesh    = self.config.get('SN', 'mesh'    )
            self.sn.factory = self.config.get('SN', 'factory' )
            self.sn.ccm     = self.config.get('SN', 'ccm'     )

            self.manufacturer_lineedit.setText(self.sn.factory)
            self.mesh_type_combo.setCurrentIndex(string.atoi(self.sn.mesh)-1)

        if  self.mode == 1:
            mesh_str = unicode(self.mesh_type_combo.currentText())
            self.mesh_type_combo.clear()
            self.mesh_type_combo.addItems([mesh_str])
            line_str = unicode(self.line_type_combo.currentText())
            self.line_type_combo.clear()
            self.line_type_combo.addItems([line_str])
            self.des_lineedit.setText(self.sn.get_sn())

        self.sync_sn_str()
        self.des_lineedit.setText(self.sn.get_sn())

    def mesh_change_sync(self):
        mesh_str = unicode(self.mesh_type_combo.currentText())
        if mesh_str == u'0x01:复合滤网\PM2.5滤网':
            new_data = '01'
        if mesh_str == u'0x02:甲醛滤网':
            new_data = '02'
        if mesh_str == u'0x03:塑料袋NFC标签':
            new_data = '03'
        if mesh_str == u'0x04:非法滤网':
            new_data = '04'
        if mesh_str == u'0xFF:没有标签':
            new_data = 'FF'
        if new_data != self.sn.mesh:
            self.sn.mesh = new_data

    def factory_change_sync(self):
        new_data = str(self.manufacturer_lineedit.text())
        if new_data != self.sn.factory:
            self.sn.factory = new_data


    def line_change_sync(self):
        new_data = str(self.line_type_combo.currentText())
        if new_data != self.sn.machine:
            self.sn.machine = new_data
            line_index = string.atoi(str(self.line_type_combo.currentText()),10)
            self.sn.sn      = self.config.get('SN', 'sn%d' % line_index )
            self.sn.number  = string.atoi(self.sn.sn[3:],16)
            self.des_lineedit.setText(self.sn.get_sn())
            print "machine change"

    def sync_sn_str(self):
        self.mesh_change_sync()
        self.factory_change_sync()
        self.line_change_sync()

        new_data = str(self.time_lineedit.text())
        new_data = new_data[2:]
        new_data = new_data.replace('-','')
        new_data = new_data.replace(' ','')
        if new_data!= self.sn.date:
            self.sn.date = new_data
        if new_data[0:4] != self.sn.date[0:4]:
            self.sn.number = 0
            self.des_lineedit.setText(self.sn.get_sn())
            print "date clear"

    def config_data_sync(self):
        self.sync_sn_str()
        self.des_lineedit.setText(self.sn.get_sn())
        line_index = string.atoi(str(self.line_type_combo.currentText()),10)

        if self.config != None:
            self.config.set('SN', 'date'   , self.sn.date    )
            self.config.set('SN', 'machine', self.sn.machine )
            self.config.set('SN', 'mesh'   , self.sn.mesh    )
            self.config.set('SN', 'factory', self.sn.factory )
            self.config.set('SN', 'sn%d' % line_index , self.sn.get_sn())

            self.config.write(open(self.config_file_name,"w"))

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = sn_ui(16,1)
    datburner.show()
    app.exec_()




