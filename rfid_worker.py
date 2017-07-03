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
    filemode = 'a',
    format = u'【%(asctime)s】 %(message)s',
)

class s_cmd_mechine(QObject):
    def __init__(self,led_dict,parent=None):
        super(s_cmd_mechine, self).__init__(parent)
        self.led_dict       = led_dict
        self.cmd_status     = [0,0,0,0]
        self.old_cmd_status = [0,0,0,0]
        self.tag_uid        = ['','','','']
        self.write_tag_cmd_count = 0
        self.write_tag_start_flag  = 0
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
        self.beep_1_cmd  = "5A 01 01 00 CA"
        # self.beep_1_cmd  = "5A 01 01 01 CA"
        self.beep_1_cmd  = self.beep_1_cmd.replace(' ','')
        self.beep_1_cmd  = self.beep_1_cmd.decode("hex")
        self.beep_3_cmd  = "5A 01 02 03 CA"
        self.beep_3_cmd  = self.beep_3_cmd.replace(' ','')
        self.beep_3_cmd  = self.beep_3_cmd.decode("hex")

        self.cmd_dict    = {
            "connect"   :self.connect_cmd   ,
            "disconnect":self.disconnect_cmd,
            "read_uid"  :self.read_uid_cmd  ,
            "set_tag"   :self.set_tag_cmd   ,
            "clear_tag" :self.clear_tag_cmd ,
            "beep_1"    :self.beep_1_cmd    ,
            "beep_3"    :self.beep_3_cmd
        }

    def get_cmd_status(self):
        max_cmd_status = self.cmd_status[0]
        min_cmd_status = self.cmd_status[0]
        for item in self.cmd_status:
            if max_cmd_status < item:
                max_cmd_status = item
            if min_cmd_status > item:
                min_cmd_status = item
        return max_cmd_status,min_cmd_status

    def get_cmd(self):
        self.emit(SIGNAL('sn_update(int,int,int,int)'),
            self.cmd_status[0],self.cmd_status[1],self.cmd_status[2],self.cmd_status[3])
        send_cmd_name = None

        max_status,min_status = self.get_cmd_status()

        if max_status == 2 and min_status == 2:
            send_cmd_name = "read_uid"
            return send_cmd_name,self.cmd_dict[send_cmd_name]

        if max_status == 3 and min_status == 1:
            send_cmd_name = "read_uid"
            return send_cmd_name,self.cmd_dict[send_cmd_name]

        if min_status == 1:
            send_cmd_name = "set_tag"
            if self.write_tag_start_flag == 0:
                self.write_tag_cmd_count = 0
                self.write_tag_start_flag = 1
            else:
                self.write_tag_cmd_count = self.write_tag_cmd_count + 1
                if self.write_tag_cmd_count >= 5:
                    self.write_tag_cmd_count = 0
                    self.write_tag_start_flag = 0

            return send_cmd_name,self.cmd_dict[send_cmd_name]

        if min_status == 0:
            send_cmd_name = "read_uid"
            return send_cmd_name,self.cmd_dict[send_cmd_name]

        if min_status == 2 or min_status == 3:
            send_cmd_name = "read_uid"
            return send_cmd_name,self.cmd_dict[send_cmd_name]

        if send_cmd_name:
            return send_cmd_name,self.cmd_dict[send_cmd_name]
        else:
            return None,None

class ComWork(QDialog):
    def __init__(self,parent=None):
        global ser
        super(ComWork,self).__init__(parent)

        self.config = ConfigParser.ConfigParser()
        self.config_file_name = os.path.abspath("./") + '\\data\\' + '\\config\\' + 'config.inf'
        self.config.readfp(open(self.config_file_name, "rb"))

        input_count       = 0
        self.ser_list     = []
        self.monitor_dict = {}
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
        self.config_data_update()

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

        self.led_status_sync()

        self.e_button.clicked.connect(self.clear_text)
        self.connect(self.send_cmd_machine,SIGNAL('sn_update(int,int,int,int)'),self.update_result )

        self.timer = QTimer()
        self.timer.timeout.connect(self.uart_auto_send_script)
        self.timer.start(600)

    def update_result(self,status1,status2,status3,status4):
        status = [status1,status2,status3 ,status4]

        i = 0
        max_status,min_status = self.send_cmd_machine.get_cmd_status()

        if max_status == 0:
            self.send_cmd_machine.write_tag_start_flag = 0

        if max_status == 2 and min_status == 2:
            for item in self.led_dict:
                i = i + 1
                self.led_dict[i].set_color("green")
            self.conf_frame.sn.number = self.conf_frame.sn.number + 1
            self.sync_sn_str()
            self.conf_frame.des_lineedit.setText(self.conf_frame.sn.get_sn())
            i = 0
            for item in self.ser_list:
                if self.monitor_dict.has_key(item):
                    if self.monitor_dict[item].com.isOpen() == True:
                        self.monitor_dict[item].com.write(self.send_cmd_machine.cmd_dict["beep_1"])
                i = i + 1
        else:
            if self.send_cmd_machine.write_tag_start_flag == 0:
                i = 0
                for item in status:
                    if status[i] == 2:
                        self.led_dict[i+1].set_color('green')
                    if status[i] == 1:
                        self.led_dict[i+1].set_color('red')
                    if status[i] == 0:
                        self.led_dict[i+1].set_color('blue')
                    i = i + 1

    def uart_auto_send_script(self):
        max_status,min_status = self.send_cmd_machine.get_cmd_status()
        cmd_status_str = 'status: [ %d %d %d %d] cmd: ' % \
           (self.send_cmd_machine.cmd_status[0],self.send_cmd_machine.cmd_status[1],
            self.send_cmd_machine.cmd_status[2],self.send_cmd_machine.cmd_status[3])

        cmd_name,send_cmd = self.send_cmd_machine.get_cmd()
        cmd_status_str = cmd_status_str + cmd_name
        print cmd_status_str

        logging.debug( "%s" % cmd_status_str )

        if send_cmd == self.send_cmd_machine.set_tag_cmd:
            send_cmd =  self.conf_frame.sn.get_tag_cmd()
            print "TAG_CMD = " + send_cmd
            logging.debug( u"TAG_CMD = %s" % send_cmd )
            send_cmd = send_cmd.decode("hex")

        i = 0
        for item in self.ser_list:
            if self.monitor_dict.has_key(item):
                if self.monitor_dict[item].com.isOpen() == True:
                    if send_cmd:
                        if max_status != 3:
                            if self.send_cmd_machine.cmd_status[i] == min_status:
                                self.monitor_dict[item].com.write(send_cmd)
                        else:
                            self.monitor_dict[item].com.write(send_cmd)
            i = i + 1

    def uart_cmd_decode(self,port,data):
        port = str(port)
        data = str(data)
        # print port,data,
        log_str = u"[%s]: %s " % (port,data)
        print log_str,

        # 获取当前串口对应的标签号
        i = 0
        for item in self.ser_list:
            i = i + 1
            if item == port:
                ser_index = i

        # 解析读取UID指令对应的返回
        if data[2:4] == '06': # 读取UID指令
            # print data[4:12]
            if data[4:12] == '00000000':
                self.send_cmd_machine.old_cmd_status[ser_index-1] = self.send_cmd_machine.cmd_status[ser_index-1]
                self.send_cmd_machine.cmd_status[ser_index-1] = 0
                if self.send_cmd_machine.old_cmd_status[ser_index-1] == 0:
                    result_str = u"读取UID FAIL"
                else:
                    result_str =u"匹配UID FIAL！标签移开"
            else:
                self.send_cmd_machine.old_cmd_status[ser_index-1] = self.send_cmd_machine.cmd_status[ser_index-1]
                self.send_cmd_machine.cmd_status[ser_index-1] = 1
                if self.send_cmd_machine.old_cmd_status[ser_index-1] == 0:
                    self.send_cmd_machine.tag_uid[ser_index-1] = data[4:12]
                    result_str = u"读取UID OK，记录UID！"
                else:
                    if self.send_cmd_machine.tag_uid[ser_index-1] == data[4:12]:
                        self.send_cmd_machine.cmd_status[ser_index-1] = 3
                    result_str = u"匹配UID OK！标签未移开"

        if data[2:4] == '0D':
            # print "WRITE_TAG = %s CHECK_TAG = %s" % (self.conf_frame.sn.get_tag(),data[4:30])
            self.send_cmd_machine.old_cmd_status[ser_index-1] = self.send_cmd_machine.cmd_status[ser_index-1]
            if data[4:30] == self.conf_frame.sn.get_tag():
                result_str = u"验证标签TAG OK"
                self.send_cmd_machine.cmd_status[ser_index-1] = 2
            else:
                result_str = u"验证标签TAG FAIL"
                self.send_cmd_machine.cmd_status[ser_index-1] = 3

        # 解析其他结果的返回
        if data[2:4] == '02':
            if data[4:8] == '0D01': # 打开串口OK
                result_str = u"打开串口OK"
            if data[4:8] == '0D02': # 打开串口失败
                result_str = u"打开串口失败"
            if data[4:8] == 'CC01': # 关闭串口OK
                result_str = u"关闭串口OK"
            if data[4:8] == '2D01': # 设置标签TAG OK
                self.send_cmd_machine.cmd_status[ser_index-1] = 2
                result_str = u"设置标签TAG OK"
            if data[4:8] == '2D04': # 设置标签TAG FAIL
                self.send_cmd_machine.cmd_status[ser_index-1] = 1
                result_str = u"设置标签TAG FAIL"
        print result_str
        logging.debug( u"%s %s" % (log_str,result_str) )

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

        line_str = str(self.conf_frame.line_type_combo.currentText())
        self.conf_frame.sn.machine = line_str

    def led_status_sync(self):
        index = 0
        for item in self.ser_list:
            index = index + 1
            if self.monitor_dict.has_key(item):
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
        port1 = self.config.get('serial', 'port1' )
        port2 = self.config.get('serial', 'port2' )
        port3 = self.config.get('serial', 'port3' )
        port4 = self.config.get('serial', 'port4' )
        self.ser_list.append(port1)
        self.ser_list.append(port2)
        self.ser_list.append(port3)
        self.ser_list.append(port4)

        print self.ser_list

        for item in self.ser_list:
            ser = None
            try:
                ser = serial.Serial( item, 115200, timeout = 0.5)
                # s.close()
            except serial.SerialException:
                pass
            if ser:
                self.monitor_dict[item] = ComMonitor(ser)
                print u"启动串口监听线程! %s " % item
                self.connect( self.monitor_dict[item],
                        SIGNAL('r_cmd_message(QString,QString)'),
                        self.uart_cmd_decode)
                self.monitor_dict[item].start()
            else:
                print u"创建串口监听线程! %s 失败，请检查设备是否接上或者更改变" % item

        self.conf_frame.sn.machine = self.config.get('SN', 'machine' )
        self.conf_frame.sn.number  = string.atoi(self.config.get('SN', 'number'  ))
        self.conf_frame.sn.mesh    = self.config.get('SN', 'mesh'    )
        self.conf_frame.sn.factory = self.config.get('SN', 'factory' )
        self.conf_frame.sn.ccm = self.config.get('SN', 'ccm' )
        print self.conf_frame.sn
        self.conf_frame.manufacturer_lineedit.setText(self.conf_frame.sn.factory)
        self.conf_frame.line_type_combo.setCurrentIndex(string.atoi(self.conf_frame.sn.machine)-1)
        self.conf_frame.mesh_type_combo.setCurrentIndex(string.atoi(self.conf_frame.sn.mesh)-1)
        self.conf_frame.ccm_type_combo.setCurrentIndex(string.atoi(self.conf_frame.sn.ccm)-1)
        mesh_str = unicode(self.conf_frame.mesh_type_combo.currentText())
        self.conf_frame.mesh_type_combo.clear()
        self.conf_frame.mesh_type_combo.addItems([mesh_str])
        ccm_str = unicode(self.conf_frame.ccm_type_combo.currentText())
        self.conf_frame.ccm_type_combo.clear()
        self.conf_frame.ccm_type_combo.addItems([ccm_str])
        line_str = unicode(self.conf_frame.line_type_combo.currentText())
        self.conf_frame.line_type_combo.clear()
        self.conf_frame.line_type_combo.addItems([line_str])
        self.sync_sn_str()
        self.conf_frame.des_lineedit.setText(self.conf_frame.sn.get_sn())

    def clear_text(self):
        print "exit"
        self.close()

    @staticmethod
    def work_start(parent = None):
        comsetting_dialog = ComWork(parent)
        result = comsetting_dialog.exec_()
        comsetting_dialog.conf_frame.config_data_sync()
        for item in comsetting_dialog.ser_list:
            if comsetting_dialog.monitor_dict.has_key(item):
                comsetting_dialog.monitor_dict[item].com.close()
                comsetting_dialog.monitor_dict[item].quit()



