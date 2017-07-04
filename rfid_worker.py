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
CONF_FONT_SIZE = 16

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = log_name,
    filemode = 'a',
    format = u'【%(asctime)s】 %(message)s',
)

MESH_IDLE       = 0
MESH_MOVE_IN    = 1
MESH_SET_TAG    = 2
MESH_SET_OK     = 3
MESH_SET_FAIL   = 4
MESH_CHECK_SHOW = 5
MESH_MOVE_OUT   = 6
MESH_MOVE_OVER  = 7

TAG_IDLE       = 0
TAG_MOVE_IN    = 1
TAG_SET_TAG    = 2
TAG_SET_OK     = 3
TAG_SET_FAIL   = 4
TAG_CHECK_OK   = 5
TAG_CHECK_FAIL = 6
TAG_MOVE_OUT   = 7
TAG_MOVE_OVER  = 8

class MeshStatus(QObject):
    def __init__(self,parent=None):
        super(MeshStatus, self).__init__(parent)
        self.mesh_status = MESH_IDLE
        self.tag_status_list = []
        self.tag_index_list  = [0,0,0,0]
        self.tag_status      = [TAG_IDLE,TAG_IDLE,TAG_IDLE,TAG_IDLE]
        # self.tag_old_status  = [TAG_IDLE,TAG_IDLE,TAG_IDLE,TAG_IDLE]
        self.set_tag_count  = 0
        self.connect_cmd    = "5A 02 0D 01 0E CA"
        self.disconnect_cmd = "5A 02 CC 01 CF CA"
        self.read_uid_cmd   = "5A 03 55 49 44 5B CA"
        self.set_tag_cmd    = "5A 09 06 0F 42 40 17 06 09 01 01 1A CA"
        self.clear_tag_cmd  = "5A 04 00 00 3D 01 38 CA"
        self.beep_1_cmd     = "5A 01 01 00 CA"
        self.beep_3_cmd     = "5A 01 02 03 CA"
        self.cmd_dict       = {
            "CONNECT"   :self.connect_cmd   ,
            "DISCONNECT":self.disconnect_cmd,
            "READ_ID"   :self.read_uid_cmd  ,
            "SET_TAG"   :self.set_tag_cmd   ,
            "CLEAR_TAG" :self.clear_tag_cmd ,
            "BEEP1"     :self.beep_1_cmd    ,
            "BEEP3"     :self.beep_3_cmd
        }

    def update_tag_status(self,tag_index,new_status):
        self.tag_status[tag_index] = new_status

    def get_max_min_tag_status(self):
        max_status = self.tag_status[0]
        min_status = self.tag_status[0]
        for item in self.tag_status:
            if max_status < item:
                max_status = item
            if min_status > item:
                min_status = item
        return max_status,min_status

    def get_mesh_status(self):
        max_s,min_s = self.get_max_min_tag_status()
        if max_s == TAG_IDLE:
            self.mesh_status = MESH_IDLE
            return self.mesh_status

        if max_s == TAG_MOVE_IN and min_s == TAG_IDLE:
            self.mesh_status = MESH_MOVE_IN
            return self.mesh_status

        if max_s == TAG_MOVE_IN and min_s == TAG_MOVE_IN:
            self.mesh_status = MESH_SET_TAG
            return self.mesh_status

        if min_s == TAG_SET_TAG:
            self.mesh_status = MESH_SET_TAG
            return self.mesh_status

        if  max_s == TAG_SET_OK and min_s == TAG_SET_OK:
            self.mesh_status = MESH_SET_OK
            return self.mesh_status

        if  max_s == TAG_SET_FAIL :
            self.mesh_status = MESH_SET_FAIL
            return self.mesh_status

        if  max_s <= TAG_CHECK_FAIL and min_s >= TAG_SET_OK:
            self.mesh_status = MESH_CHECK_SHOW
            return self.mesh_status

        if  min_s == TAG_MOVE_OUT:
            self.mesh_status = MESH_MOVE_OUT
            return self.mesh_status

        if  min_s == TAG_MOVE_OVER:
            self.mesh_status = MESH_MOVE_OVER
            return self.mesh_status

    def get_cmd(self):
        self.emit(SIGNAL('sn_update(int,int,int,int)'),
            self.tag_status[0],self.tag_status[1],
            self.tag_status[2],self.tag_status[3])

        send_cmd_name = None

        mesh_status = self.get_mesh_status()

        if mesh_status == MESH_IDLE     or mesh_status == MESH_MOVE_IN or \
           mesh_status == MESH_MOVE_OUT or mesh_status == MESH_MOVE_OVER:
            send_cmd_name = "READ_ID"

        if mesh_status == MESH_SET_TAG :
            send_cmd_name = "SET_TAG"

        if mesh_status == MESH_SET_OK or mesh_status == MESH_SET_FAIL :
            send_cmd_name = "BEEP1"

        if mesh_status == MESH_CHECK_SHOW :
            send_cmd_name = "BEEP3"

        if send_cmd_name:
            return send_cmd_name,self.cmd_dict[send_cmd_name]
        else:
            return None,None

class ComWork(QDialog):
    def __init__(self,parent=None):
        super(ComWork,self).__init__(parent)
        self.ser_list     = []
        self.monitor_dict = {}
        self.ser          = None
        self.ComMonitor   = None
        self.mesh_s       = MeshStatus()

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
        self.config = ConfigParser.ConfigParser()
        self.config_file_name = os.path.abspath("./") + '\\data\\' + '\\config\\' + 'config.inf'
        self.config.readfp(open(self.config_file_name, "rb"))

        self.conf_frame = sn_ui( 16,1,self.config, self.config_file_name )
        self.config_data_update()
        self.tag_frame  = tag_ui( self.config, self.config_file_name )

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
        box.addWidget(self.tag_frame)
        box.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addLayout(e_layout)
        box.addItem(QSpacerItem(30,30,QSizePolicy.Expanding,QSizePolicy.Minimum))
        box.addWidget(self.zkxl_label)
        box.addItem(QSpacerItem(30,30,QSizePolicy.Expanding,QSizePolicy.Minimum))

        self.setLayout(box)

        self.e_button.clicked.connect(self.clear_text)

        self.timer = QTimer()
        self.timer.timeout.connect(self.uart_auto_send_script)
        self.timer.start(500)

    def update_led_status(self):
        status = self.mesh_s.tag_status

        mesh_status = self.mesh_s.get_mesh_status()
        print mesh_status,status
        if mesh_status:
            logging.debug( u"MESH:%d TAG:[%d %d %d %d]" % (mesh_status,status[0],status[1],status[2],status[3]) )

        # 空闲状态显示
        if mesh_status == MESH_IDLE :
            i = 0
            for item in status:
                self.tag_frame.tag.led_list[i].set_color('gray')
                i = i + 1
            return

        # 设置卡片 FAIL
        if mesh_status == MESH_SET_FAIL or mesh_status == MESH_SET_OK :
            i = 0
            for item in status:
                if status[i] == TAG_SET_FAIL:
                    self.tag_frame.tag.led_list[i].set_color('red')
                if status[i] == TAG_SET_OK:
                    self.tag_frame.tag.led_list[i].set_color('green')
                i = i + 1
            return

        # 重复烧录显示
        if mesh_status == MESH_CHECK_SHOW :
            i = 0
            for item in status:
                if status[i] == TAG_CHECK_OK:
                    self.tag_frame.tag.led_list[i].set_color('green')
                else:
                    self.tag_frame.tag.led_list[i].set_color('red')
                i = i + 1
            return

        # 移入显示
        if mesh_status == MESH_MOVE_IN :
            i = 0
            for item in status:
                if status[i] == TAG_MOVE_IN :
                    self.tag_frame.tag.led_list[i].set_color('blue')
                i = i + 1
            return

        # 移出显示
        if mesh_status == MESH_MOVE_OUT or mesh_status == MESH_MOVE_OVER:
            i = 0
            for item in status:
                if status[i] == TAG_MOVE_OVER :
                    self.tag_frame.tag.led_list[i].set_color('gray')
                i = i + 1
            return

    def uart_auto_send_script(self):
        self.update_led_status()

        mesh_status = self.mesh_s.mesh_status

        cmd_name,send_cmd = self.mesh_s.get_cmd()
        print cmd_name,send_cmd
        logging.debug( u"%s: %s" % (cmd_name,send_cmd) )
        if send_cmd:
            send_cmd = send_cmd.replace(' ','')
            send_cmd = send_cmd.decode("hex")

        if mesh_status == MESH_SET_TAG:
            send_cmd =  self.conf_frame.sn.get_tag_cmd()
            print "TAG_CMD = " + send_cmd
            logging.debug( u"TAG_CMD = %s" % send_cmd )
            send_cmd = send_cmd.decode("hex")

            i = 0
            for item in self.ser_list:
                if self.monitor_dict.has_key(item):
                    if self.monitor_dict[item].com.isOpen() == True:
                        if self.mesh_s.tag_status[i] == TAG_MOVE_IN or \
                           self.mesh_s.tag_status[i] == TAG_SET_TAG:
                            self.monitor_dict[item].com.write(send_cmd)
                i = i + 1
            return

        if mesh_status == MESH_MOVE_IN or mesh_status == MESH_MOVE_OVER :
            i = 0
            for item in self.ser_list:
                if self.monitor_dict.has_key(item):
                    if self.monitor_dict[item].com.isOpen() == True:
                        if self.mesh_s.tag_status[i] == TAG_IDLE or \
                           self.mesh_s.tag_status[i] == TAG_MOVE_OVER:
                            if send_cmd:
                                self.monitor_dict[item].com.write(send_cmd)
                i = i + 1
            return

        if mesh_status == MESH_MOVE_OUT:
            i = 0
            for item in self.ser_list:
                if self.monitor_dict.has_key(item):
                    if self.monitor_dict[item].com.isOpen() == True:
                        if self.mesh_s.tag_status[i] == TAG_MOVE_OUT:
                            if send_cmd:
                                self.monitor_dict[item].com.write(send_cmd)
                i = i + 1
            return

        if mesh_status == MESH_IDLE:
            i = 0
            for item in self.ser_list:
                if self.monitor_dict.has_key(item):
                    if self.monitor_dict[item].com.isOpen() == True:
                        if send_cmd:
                            self.monitor_dict[item].com.write(send_cmd)
                i = i + 1
            return

        if mesh_status == MESH_SET_OK or mesh_status == MESH_SET_FAIL  or \
           mesh_status == MESH_CHECK_SHOW:
            self.mesh_s.set_tag_count = self.mesh_s.set_tag_count + 1
            i = 0
            if self.mesh_s.set_tag_count > 3:
                for item in self.ser_list:
                    self.mesh_s.update_tag_status(i,TAG_MOVE_OUT)
                    i = i + 1
                self.mesh_s.set_tag_count = 0

            i = 0
            for item in self.ser_list:
                if self.monitor_dict.has_key(item):
                    if self.monitor_dict[item].com.isOpen() == True:
                        if self.mesh_s.set_tag_count == 0:
                            if send_cmd:
                                self.monitor_dict[item].com.write(send_cmd)
                i = i + 1

            if mesh_status == MESH_SET_OK :
                # 序列号增加
                if self.mesh_s.set_tag_count == 0:
                    self.conf_frame.sn.number = self.conf_frame.sn.number + 1
                    self.sync_sn_str()
                    self.conf_frame.des_lineedit.setText(self.conf_frame.sn.get_sn())
            return

    def uart_cmd_decode(self,port,data):
        port = str(port)
        data = str(data)

        mesh_status = self.mesh_s.mesh_status

        log_str = u"[%s]: %s " % (port,data)
        print log_str,

        # 获取当前串口对应的标签号
        i = 0
        for item in self.ser_list:
            if item == port:
                ser_index = i
            i = i + 1

        # 解析读取UID指令对应的返回
        if data[2:4] == '06': # 读取UID指令
            # print data[4:12]
            if data[4:12] == '00000000':
                if mesh_status == MESH_IDLE or mesh_status == MESH_MOVE_IN or mesh_status == MESH_MOVE_OVER:
                    result_str = u"读取UID FAIL"
                    self.mesh_s.update_tag_status(ser_index,TAG_IDLE)
                if mesh_status == MESH_MOVE_OUT:
                    self.mesh_s.update_tag_status(ser_index,TAG_MOVE_OVER)
                    result_str = u"匹配UID FIAL！标签移开"
            else:
                if mesh_status == MESH_IDLE or mesh_status == MESH_MOVE_IN or mesh_status == MESH_MOVE_OVER:
                    self.mesh_s.update_tag_status(ser_index,TAG_MOVE_IN)
                    result_str = u"读取UID OK，记录UID！"
                if mesh_status == MESH_MOVE_OUT:
                    self.mesh_s.update_tag_status(ser_index,TAG_MOVE_OUT)
                    result_str = u"匹配UID OK！标签未移开"

        if data[2:4] == '0D':
            if data[4:30] == self.conf_frame.sn.get_tag():
                result_str = u"验证标签TAG OK"
                self.mesh_s.update_tag_status(ser_index,TAG_CHECK_OK)
            else:
                result_str = u"验证标签TAG FAIL"
                self.mesh_s.update_tag_status(ser_index,TAG_CHECK_FAIL)

        # 解析其他结果的返回
        if data[2:4] == '02':
            if data[4:8] == '0D01': # 打开串口OK
                result_str = u"打开串口OK"
            if data[4:8] == '0D02': # 打开串口失败
                result_str = u"打开串口失败"
            if data[4:8] == 'CC01': # 关闭串口OK
                result_str = u"关闭串口OK"
            if data[4:8] == '2D01': # 设置标签TAG OK
                self.mesh_s.update_tag_status(ser_index,TAG_SET_OK)
                result_str = u"设置标签TAG OK"
            if data[4:8] == '2D04': # 设置标签TAG FAIL
                self.mesh_s.update_tag_status(ser_index,TAG_SET_TAG)
                self.mesh_s.set_tag_count = self.mesh_s.set_tag_count + 1
                if self.mesh_s.set_tag_count > 5:
                    self.mesh_s.update_tag_status(ser_index,TAG_SET_FAIL)
                    self.mesh_s.set_tag_count = 0
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

    def config_data_update(self):
        port1 = self.config.get('serial', 'port1' )
        port2 = self.config.get('serial', 'port2' )
        port3 = self.config.get('serial', 'port3' )
        port4 = self.config.get('serial', 'port4' )
        self.ser_list.append(port1)
        self.ser_list.append(port2)
        self.ser_list.append(port3)
        self.ser_list.append(port4)

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
        self.conf_frame.sn.ccm     = self.config.get('SN', 'ccm' )
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



