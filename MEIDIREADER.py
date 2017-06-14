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
from JsonDecode   import *

ser           = 0
input_count   = 0
LOGTIMEFORMAT = '%Y%m%d%H'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = log_name,
    filemode = 'w',
    format = u'【%(asctime)s】 %(message)s',
)

class UartListen(QThread):
    def __init__(self,parent=None):
        super(UartListen,self).__init__(parent)
        self.working       = True
        self.num           = 0
        self.json_revice   = JsonDecode()
        self.ReviceFunSets = { 0:self.decode }

    def __del__(self):
        self.working=False
        self.wait()

    def decode(self,read_char):
        recv_str      = ""
        ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'

        str1 = self.json_revice.r_machine(read_char)

        if len(str1) != 0:
            now = time.strftime( ISOTIMEFORMAT,
                time.localtime(time.time()))
            recv_str = u"R[%d]: %s" % (input_count-1,str1)
        return recv_str

    def run(self):
        global ser
        global input_count

        while self.working==True:
            if input_count   >= 1:
                try:
                    read_char = ser.read(1)
                except serial.SerialException:
                    input_count = 0
                    cmd = u'{"fun":"Error","description":"serialport lost!"}'
                    recv_str = u"R[%d]: %s" % (input_count-1,cmd)
                    pass
                if input_count > 0:
                    recv_str  = self.ReviceFunSets[0]( read_char )
                if recv_str :
                    self.emit(SIGNAL('output(QString)'),recv_str)

class MEIDIREADER(QWidget):
    def __init__(self, parent=None):
        global ser

        super(MEIDIREADER, self).__init__(parent)
        input_count         = 0
        self.ports_dict     = {}
        self.dtq_id         = ''
        self.setWindowTitle(u"滤网RFID发卡工具v1.0")

        self.com_combo=QComboBox(self)
        self.com_combo.setFixedSize(75, 20)
        self.uart_scan(self.ports_dict)
        self.start_button = QPushButton(u"打开发卡器")
        self.clear_button = QPushButton(u"清空LOG信息")
        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.com_combo)
        c_hbox.addWidget(self.start_button)
        c_hbox.addWidget(self.clear_button)

        self.op_label=QLabel(u"操作类型  :")
        self.op_combo=QComboBox(self)
        self.op_combo.addItems([u'0x00:读取UID',u'0x01:写入DES秘钥',
            u'0x02:读取TAG数据',u'0x03:写入TAG数据'])
        self.op_label.setFixedSize(65, 20)
        self.op_button = QPushButton(u"发送指令")
        d_hbox = QHBoxLayout()
        d_hbox.addWidget(self.op_label)
        d_hbox.addWidget(self.op_combo)
        d_hbox.addWidget(self.op_button)
        op_frame = QFrame()
        op_frame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        op_frame.setLayout(d_hbox)

        self.dtq_id_label=QLabel(u"滤网序列号:")
        self.dtq_id_lineedit = QLineEdit(u"11223344")
        self.time_label=QLabel(u"生产日期:")
        self.manufacturer_label=QLabel(u"生产厂家  :")
        self.manufacturer_lineedit = QLineEdit()
        self.mesh_type_label=QLabel(u"滤网类型:")
        self.mesh_type_combo = QComboBox()
        self.mesh_type_combo.addItems([u'0x01:复合滤网\PM2.5滤网',u'0x02:甲醛滤网',
            u'0x03:塑料袋NFC标签',u'0x04:非法滤网',u'0xFF:没有标签'])
        self.des_label=QLabel(u"DES秘钥   :")
        self.des_lineedit = QLineEdit()
        self.time_lineedit = QLineEdit( time.strftime(
            '%Y-%m-%d ',time.localtime(time.time())))
        g_hbox = QGridLayout()
        g_hbox.addWidget(self.dtq_id_label         ,0,0)
        g_hbox.addWidget(self.dtq_id_lineedit      ,0,1)
        g_hbox.addWidget(self.time_label           ,0,2)
        g_hbox.addWidget(self.time_lineedit        ,0,3)
        g_hbox.addWidget(self.manufacturer_label   ,1,0)
        g_hbox.addWidget(self.manufacturer_lineedit,1,1)
        g_hbox.addWidget(self.mesh_type_label      ,1,2)
        g_hbox.addWidget(self.mesh_type_combo      ,1,3)
        g_hbox.addWidget(self.des_label            ,2,0)
        g_hbox.addWidget(self.des_lineedit         ,2,1,2,3)
        conf_frame = QFrame()
        conf_frame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        conf_frame.setLayout(g_hbox)

        self.check_browser_label=QLabel(u"数据校验:")
        self.check_browser_label.setFixedHeight(20)
        self.check_browser = QTextEdit()
        self.check_browser.setFont(QFont("Courier New", 10, QFont.Bold))
        self.check_browser.document().setMaximumBlockCount (1000);
        self.check_browser.setFixedHeight(60)
        b_vbox = QVBoxLayout()
        b_vbox.addWidget(self.check_browser_label )
        b_vbox.addWidget(self.check_browser       )

        self.log_browser_label=QLabel(u"LOG日志 :")
        self.log_browser = QTextBrowser()
        self.log_browser.setFont(QFont("Courier New", 10, QFont.Bold))
        self.log_browser.document().setMaximumBlockCount (1000);

        l_vbox = QVBoxLayout()
        l_vbox.addWidget(self.log_browser_label)
        l_vbox.addWidget(self.log_browser)

        box = QVBoxLayout()
        box.addLayout(c_hbox)
        box.addWidget(conf_frame)
        box.addWidget(op_frame)
        box.addLayout(b_vbox)
        box.addLayout(l_vbox)
        self.setLayout(box)
        self.resize( 530, 500 )

        self.clear_button.clicked.connect(self.clear_text)
        self.start_button.clicked.connect(self.band_start)
        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('output(QString)'),
            self.uart_update_text)
        self.com_combo.currentIndexChanged.connect(self.change_uart)

    def uart_scan(self,dict):
        for i in range(256):

            try:
                s = serial.Serial(i)
                if dict.has_key(s.portstr) == False:
                    self.com_combo.addItem(s.portstr)
                    self.ports_dict[s.portstr] = i
                s.close()
            except serial.SerialException:
                pass

    def clear_text(self):
        self.log_browser.clear()

    def uart_update_text(self,data):
        json_dict = {}
        if data[0] == 'R':
            json_str = data[6:]
            print json_str
        else:
            self.log_browser.append(data)

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
            ser = serial.Serial( self.ports_dict[serial_port], 1152000)
        except serial.SerialException:
            pass

        if mode == 1:
            if ser.isOpen() == True:
                self.start_button.setText(u"关闭发卡器")
                self.uart_listen_thread.start()
                input_count = input_count + 1
        else:
            self.start_button.setText(u"打开发卡器")
            input_count = 0
            ser.close()

    def band_start(self):
        global ser
        global input_count

        button = self.sender()
        button_str = button.text()

        if button_str == u"打开发卡器":
            self.setting_uart(1)
            if ser.isOpen() == True:
                self.uart_listen_thread.start()
                cmd = "{'fun':'bind_start'}"
                ser.write(cmd)
                input_count = input_count + 1
                data = u"S[%d]: " % (input_count-1) + u"%s" % cmd
                return

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = MEIDIREADER()
    datburner.show()
    app.exec_()
    cmd = '{"fun": "si24r2e_auto_burn","setting": "0"}'
    if ser != 0:
        try:
            ser.write(cmd)
        except serial.SerialException:
            pass
        datburner.setting_uart(0)



