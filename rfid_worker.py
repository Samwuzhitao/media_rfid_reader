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

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = log_name,
    filemode = 'w',
    format = u'【%(asctime)s】 %(message)s',
)

class s_cmd_mechine(QObject):
    def __init__(self,led_dict,parent=None):
        super(s_cmd_mechine, self).__init__(parent)
        self.led_dict    = led_dict
        self.cmd_status  = [0,0,0,0]
        self.send_cmd_count = 0
        self.status      = ['blue','blue','blue','blue']
        self.connect_cmd = "5A 02 0D 01 0E CA"
        self.connect_cmd = self.connect_cmd.replace(' ','')
        self.connect_cmd = self.connect_cmd.decode("hex")
        self.disconnect_cmd = "5A 02 CC 01 CF CA"
        self.disconnect_cmd = self.disconnect_cmd.replace(' ','')
        self.disconnect_cmd = self.disconnect_cmd.decode("hex")
        self.read_uid_cmd = "5A 03 55 49 44 5B CA"
        self.read_uid_cmd = self.read_uid_cmd.replace(' ','')
        self.read_uid_cmd = self.read_uid_cmd.decode("hex")
        self.set_tag_cmd  = "5A 09 06 0F 42 40 17 06 09 01 01 1A CA"
        self.set_tag_cmd  = self.set_tag_cmd.replace(' ','')
        self.set_tag_cmd  = self.set_tag_cmd.decode("hex")
        self.clear_tag_cmd  = "5A 04 00 00 3D 01 38 CA"
        self.clear_tag_cmd  = self.clear_tag_cmd.replace(' ','')
        self.clear_tag_cmd  = self.clear_tag_cmd.decode("hex")

        self.cmd_dict    = {
            "connect"   :self.connect_cmd   ,
            "disconnect":self.disconnect_cmd,
            "read_uid"  :self.read_uid_cmd  ,
            "set_tag"   :self.set_tag_cmd   ,
            "clear_tag" :self.clear_tag_cmd
        }

    def clear_cmd_status(self):
         self.cmd_status[0]  = 0
         self.cmd_status[1]  = 0
         self.cmd_status[2]  = 0
         self.cmd_status[3]  = 0

    def get_max_cmd_status(self):
        max_cmd_status = 0
        for item in self.cmd_status:
            if max_cmd_status < item:
                max_cmd_status = item
        return max_cmd_status

    def check_cmd_status(self):
        if self.cmd_status[0] == self.cmd_status[1] and \
           self.cmd_status[1] == self.cmd_status[2] and \
           self.cmd_status[2] == self.cmd_status[3]:
           return True
        else:
            return False

    def get_cmd(self):
        self.emit(SIGNAL('sn_update(QString,QString,QString,QString)'),
            self.status[0],self.status[1],self.status[2],self.status[3])
        send_cmd_name = None
        # 指令改变，只要有一个没有寻到卡片就返回寻卡指令
        print self.cmd_status
        for item in self.cmd_status:
            if item == 0:
                send_cmd_name = "read_uid"
                return self.cmd_dict[send_cmd_name]

        print "check_cmd_status = ",self.check_cmd_status()

        sort_list = self.cmd_status
        sort_list.sort()
        if sort_list[0] == 1:
            send_cmd_name = "set_tag"

        print "cmd_status = %d cmd = %s" % (self.cmd_status[0], send_cmd_name)
        logging.debug( "cmd_status = %d cmd = %s" % (self.cmd_status[0], send_cmd_name))
        if send_cmd_name:
            return self.cmd_dict[send_cmd_name]
        else:
            return None

    def set_status(self,index,new_status):
        self.status[index-1] = new_status

class ComWork(QDialog):
    def __init__(self,ser_list,monitor_dict,parent=None):
        global ser
        super(ComWork, self).__init__(parent)

        self.config = ConfigParser.ConfigParser()
        self.config_file_name = os.path.abspath("./") + '\\data\\' + '\\config\\' + 'config.inf'
        self.config.readfp(open(self.config_file_name, "rb"))

        input_count       = 0
        self.ser_list     = ser_list
        self.monitor_dict = monitor_dict
        self.led_dict     = {}
        self.ser        = None
        self.ComMonitor = None
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
        self.led_dict[1] = self.led1
        self.com2_lable = QLabel(u"标签2")
        self.com2_lable.setAlignment(Qt.AlignCenter)
        self.com2_lable.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.led2  = LED(60)
        self.led_dict[2] = self.led2
        self.com3_lable = QLabel(u"标签3")
        self.com3_lable.setAlignment(Qt.AlignCenter)
        self.com3_lable.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.led3  = LED(60)
        self.led_dict[3] = self.led3
        self.com4_lable = QLabel(u"标签4")
        self.com4_lable.setAlignment(Qt.AlignCenter)
        self.com4_lable.setFont(QFont("Roman times",CONF_FONT_SIZE,QFont.Bold))
        self.led4  = LED(60)
        self.led_dict[4] = self.led4
        self.send_cmd_machine = s_cmd_mechine(self.led_dict)
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

        self.zkxl_label = QLabel(u"版权所有：深圳中科讯联科技股份有限公司")
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

        self.connect(self.send_cmd_machine,SIGNAL('sn_update(QString,QString,QString,QString)'),self.update_result )

        for item in self.ser_list:
            if self.monitor_dict.has_key(item):
                print u"启动串口监听线程! %s " % item
                self.connect( self.monitor_dict[item],
                        SIGNAL('r_cmd_message(QString,QString)'),
                        self.uart_cmd_decode)
                self.monitor_dict[item].start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.uart_auto_send_script)
        self.timer.start(500)

    def update_result(self,status1,status2,status3,status4):
        status = [status1,status2,status3 ,status4]
        # print status
        i = 0
        if self.send_cmd_machine.get_max_cmd_status() == 2:
            if self.send_cmd_machine.check_cmd_status() == True:
                if self.send_cmd_machine.cmd_status[0] == 2:
                    self.conf_frame.sn.number = self.conf_frame.sn.number + 1
                    # logging.debug( "cmd_status = %d cmd：" % (self.cmd_status[0],send_cmd) )
                    self.sync_sn_str()
                    self.conf_frame.des_lineedit.setText(self.conf_frame.sn.get_sn())
                    for item in self.led_dict:
                        i = i + 1
                        self.led_dict[i].set_color("green")
                        self.send_cmd_machine.clear_cmd_status()
                else:
                    for item in self.led_dict:
                        if status[i] == "green":
                            i = i + 1
                            self.led_dict[i].set_color('green')
                        else:
                            i = i + 1
                            self.led_dict[i].set_color('red')
        else:
            for item in self.led_dict:
                i = i + 1
                self.led_dict[i].set_color("red")

    def uart_auto_send_script(self):
        send_cmd = self.send_cmd_machine.get_cmd()
        if send_cmd == self.send_cmd_machine.set_tag_cmd:
            send_cmd =  self.conf_frame.sn.get_tag_cmd()
            print "TAG_CMD = " + send_cmd
            send_cmd = send_cmd.decode("hex")
        if send_cmd:
            i = 0
            for item in self.ser_list:
                if self.monitor_dict.has_key(item):
                    if self.monitor_dict[item].com.isOpen() == True:
                        if self.send_cmd_machine.cmd_status[i] != 2:
                            self.monitor_dict[item].com.write(send_cmd)
                i = i + 1


    def uart_cmd_decode(self,port,data):
        port = str(port)
        data = str(data)
        print port,data

        # 获取当前串口对应的标签号
        i = 0
        for item in self.ser_list:
            i = i + 1
            if item == port:
                ser_index = i

        # 解析读取UID指令对应的返回
        if data[2:4] == '06': # 读取UID指令
            print data[4:12]
            if data[4:12] == '00000000':
                self.send_cmd_machine.set_status(ser_index,"blue")
                self.send_cmd_machine.cmd_status[ser_index-1] = 0
            else:
                self.send_cmd_machine.set_status(ser_index,"green")
                self.send_cmd_machine.cmd_status[ser_index-1] = 1

        if data[2:4] == '0D':
            print "WRITE_TAG = %s CHECK_TAG = %s" % (self.conf_frame.sn.get_tag(),data[4:30])
            if data[4:30] == self.conf_frame.sn.get_tag():
                print "验证标签TAG OK"
                self.send_cmd_machine.cmd_status[ser_index-1] = 2
            else:
                print "验证标签TAG FAIL"
                self.send_cmd_machine.cmd_status[ser_index-1] = 0

        # # 解析其他结果的返回
        if data[2:4] == '02':
            if data[4:8] == '0D01': # 打开串口OK
                self.led_dict[ser_index].set_color("green")
            if data[4:8] == '0D02': # 打开串口失败
                self.led_dict[ser_index].set_color("blue")
            if data[4:8] == 'CC01': # 关闭串口OK
                self.led_dict[ser_index].set_color("blue")
            if data[4:8] == '2D01': # 设置标签TAG OK
                self.led_dict[ser_index].set_color("green")
                self.send_cmd_machine.cmd_status[ser_index-1] = 2
                print "设置标签TAG OK"
            if data[4:8] == '2D04': # 设置标签TAG FAIL
                self.led_dict[ser_index].set_color("red")
                self.send_cmd_machine.cmd_status[ser_index-1] = 1
                print "设置标签TAG FAIL"

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

    @staticmethod
    def work_start(ser_list,monitor_dict,parent = None):
        comsetting_dialog = ComWork(ser_list,monitor_dict,parent)
        result = comsetting_dialog.exec_()
        for item in ser_list:
            comsetting_dialog.monitor_dict[item].com.close()
            comsetting_dialog.monitor_dict[item].quit()



