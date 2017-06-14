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
from HexDecode   import *

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
        self.hex_revice    = HexDecode()
        self.ReviceFunSets = { 0:self.cmd_decode }

    def __del__(self):
        self.working=False
        self.wait()

    def cmd_decode(self,read_char):
        ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'
        recv_str = self.hex_revice.r_machine(read_char)

        if recv_str :
            now = time.strftime( ISOTIMEFORMAT,
                time.localtime(time.time()))
            recv_str = u"R[%d]: %s" % (input_count-1,recv_str)
            print "REV = %s" % recv_str
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
                        self.hex_revice.clear()
                        self.emit(SIGNAL('output(QString)'),recv_str)

class MEIDIREADER(QWidget):
    def __init__(self, parent=None):
        global ser
        super(MEIDIREADER, self).__init__(parent)
        input_count         = 0
        self.ports_dict     = {}
        self.dtq_id         = ''
        self.r_cmd          = HexDecode()
        self.s_cmd          = HexDecode()
        self.s_cmd.init()
        self.setWindowTitle(u"滤网RFID发卡工具v1.0")

        self.com_combo=QComboBox(self)
        self.com_combo.setFixedSize(75, 20)
        self.uart_scan(self.ports_dict)
        self.start_button = QPushButton(u"打开串口")
        self.clear_button = QPushButton(u"清空LOG信息")
        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.com_combo)
        c_hbox.addWidget(self.start_button)
        c_hbox.addWidget(self.clear_button)

        self.op_label=QLabel(u"操作:")
        self.op_label.setFixedSize(30, 20)
        self.op_combo=QComboBox(self)
        self.op_combo.addItems([u'0x0A:读',u'0x0B:写'])
        self.type_label=QLabel(u"类型:")
        self.type_label.setFixedSize(30, 20)
        self.type_combo=QComboBox(self)
        self.type_combo.addItems([u'0x00:UID',u'0x01:DES秘钥',u'0x02:TAG数据'])
        self.type_combo.setCurrentIndex(self.type_combo.
            findText(u'0x02:TAG数据'))
        self.sync_button = QPushButton(u"同步数据")
        self.op_button = QPushButton(u"生效数据")
        d_hbox = QHBoxLayout()
        d_hbox.addWidget(self.op_label)
        d_hbox.addWidget(self.op_combo)
        d_hbox.addWidget(self.type_label)
        d_hbox.addWidget(self.type_combo)
        d_hbox.addWidget(self.sync_button)
        d_hbox.addWidget(self.op_button)
        op_frame = QFrame()
        op_frame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        op_frame.setLayout(d_hbox)

        self.dtq_id_label=QLabel(u"滤网序列号:")
        self.dtq_id_lineedit = QLineEdit(u"11 22 33 44")
        self.time_label=QLabel(u"生产日期:")
        self.manufacturer_label=QLabel(u"生产厂家  :")
        self.manufacturer_lineedit = QLineEdit(u'FF')
        self.mesh_type_label=QLabel(u"滤网类型:")
        self.mesh_type_combo = QComboBox()
        self.mesh_type_combo.addItems([u'0x01:复合滤网\PM2.5滤网',u'0x02:甲醛滤网',
            u'0x03:塑料袋NFC标签',u'0x04:非法滤网',u'0xFF:没有标签'])
        self.des_label=QLabel(u"DES秘钥   :")
        self.des_lineedit = QLineEdit(u'FF FF FF FF FF FF FF FF')
        self.time_lineedit = QLineEdit( time.strftime(
            '%Y-%m-%d',time.localtime(time.time())))

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

        self.tpye_data_sync()

        self.clear_button.clicked.connect(self.clear_text)
        self.start_button.clicked.connect(self.band_start)
        self.sync_button.clicked.connect(self.sync_cmd_to_mcu)
        self.mesh_type_combo.currentIndexChanged.connect(self.tpye_data_sync)
        self.op_combo.currentIndexChanged.connect(self.tpye_data_sync)
        self.type_combo.currentIndexChanged.connect(self.tpye_data_sync)
        # self.op_button.clicked.connect(self.find_card_start)

        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('output(QString)'),
            self.uart_update_text)
        self.com_combo.currentIndexChanged.connect(self.change_uart)

    def get_lineedit_str(self,edit,type):
        data_str = ''
        if type == 6:
            r_str = unicode(edit.currentText())
            if r_str == u'0x00:UID':
                data_str = '00'
            if r_str == u'0x01:DES秘钥':
                data_str = '01'
            if r_str == u'0x02:TAG数据':
                data_str = '02'
            # print "TYPE = %s" % data_str
            self.s_cmd.op_str = data_str

        if type == 5:
            r_str = unicode(edit.currentText())
            if r_str == u'0x0A:读':
                data_str = '0A'
            if r_str == u'0x0B:写':
                data_str = '0B'
            # print "CMD = %s" % data_str
            self.s_cmd.cmd_str = data_str

        if type == 4:
            r_str = unicode(edit.currentText())
            if r_str == u'0x01:复合滤网\PM2.5滤网':
                data_str = '01'
            if r_str == u'0x02:甲醛滤网':
                data_str = '02'
            if r_str == u'0x03:塑料袋NFC标签':
                data_str = '03'
            if r_str == u'0x04:非法滤网':
                data_str = '04'
            if r_str == u'0xFF:没有标签':
                data_str = 'FF'
            # print u"滤网类型 = %s" % data_str
            self.s_cmd.data = self.s_cmd.data + data_str
            self.s_cmd.len  = self.s_cmd.len + len(data_str)/2
            self.s_cmd.len_str = "%02X" % self.s_cmd.len

        if type == 7 or type == 3 or type == 2 or type == 1:
            data_str = str(edit.text())
            if type == 2:
                data_str = data_str[2:]
            data_str = data_str.replace('-','')
            data_str = data_str.replace(' ','')
        # print "data = %s len = %d" % (data_str,len(data_str))
            self.s_cmd.data = self.s_cmd.data + data_str
            self.s_cmd.len  = self.s_cmd.len + len(data_str)/2
            self.s_cmd.len_str = "%02X" % self.s_cmd.len

    def tag_data_sync(self):
        self.s_cmd.init()
        self.get_lineedit_str(self.dtq_id_lineedit      ,1)
        self.get_lineedit_str(self.time_lineedit        ,2)
        self.get_lineedit_str(self.manufacturer_lineedit,3)
        self.get_lineedit_str(self.mesh_type_combo      ,4)
        self.get_lineedit_str(self.op_combo             ,5)
        self.get_lineedit_str(self.type_combo           ,6)
        self.check_browser.setText(self.s_cmd.get_str()   )

    def tpye_data_sync(self):
        self.s_cmd.init()
        r_str = unicode(self.type_combo.currentText())
        if r_str == u'0x00:UID':
            self.get_lineedit_str(self.op_combo             ,5)
            self.get_lineedit_str(self.type_combo           ,6)
            self.check_browser.setText(self.s_cmd.get_str()   )
        if r_str == u'0x01:DES秘钥':
            self.get_lineedit_str(self.op_combo             ,5)
            self.get_lineedit_str(self.type_combo           ,6)
            self.get_lineedit_str(self.des_lineedit         ,7)
            self.check_browser.setText(self.s_cmd.get_str()   )
        if r_str == u'0x02:TAG数据':
            self.tag_data_sync()
  
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
        self.log_browser.append(data)
        cmd = str(data[6:])
        # decode
        cmd = cmd.decode("hex")
        for i in cmd:
            self.r_cmd.r_machine(i)
        # self.decode.format_print()
        self.log_browser.append(u"CMD = %s, TYPE= %s, DATA = %s" % \
            (self.r_cmd.cmd_str,self.r_cmd.op_str,self.r_cmd.data) )
        self.r_cmd.clear()
        # ser.write(cmd)

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
                self.log_browser.append(u"打开串口!" )
                logging.debug(u"打开串口!" )
                self.start_button.setText(u"关闭串口")
                self.uart_listen_thread.start()
                input_count = input_count + 1
        else:
            self.start_button.setText(u"打开串口")
            self.log_browser.append(u"关闭串口!" )
            logging.debug(u"关闭串口!" )
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
                self.uart_listen_thread.start()
                input_count = input_count + 1
        if button_str == u"关闭串口":
            self.setting_uart(0)

    def sync_cmd_to_mcu(self):
        global ser
        global input_count

        send_cmd = str(self.check_browser.toPlainText())
        log_str = u"S[%d]：%s" % (input_count,send_cmd)
        self.log_browser.append( log_str )
        logging.debug( log_str )

        send_cmd = str(send_cmd.replace(' ',''))
        send_cmd = send_cmd.decode("hex")
        if input_count > 0:
            ser.write(send_cmd)
            input_count = input_count + 1

    def find_card_stop(self):
        global input_count
        global ser

        send_cmd  = "5A 02 0C 00 OE CA"
        log_str   = u"S[%d]：%s" % (input_count,send_cmd)

        if input_count > 0:
            self.log_browser.append( log_str )
            logging.debug( log_str )

            send_cmd = str(send_cmd.replace(' ',''))
            send_cmd = send_cmd.decode("hex")

            ser.write(send_cmd)
            input_count = input_count + 1

    def find_card_start(self):
        global input_count
        global ser

        send_cmd = u"5A 02 0C 01 OF CA"
        log_str  = u"S[%d]：%s" % (input_count,send_cmd)

        if input_count > 0:
            self.log_browser.append( log_str )
            logging.debug( log_str )

            send_cmd = send_cmd.replace(' ','')
            send_cmd = send_cmd.decode("hex")

            ser.write(send_cmd)
            input_count = input_count + 1

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = MEIDIREADER()
    datburner.show()
    app.exec_()

    if ser != 0:
        # datburner.find_card_stop()
        datburner.setting_uart(0)



