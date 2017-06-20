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

from HexDecode  import *
from ComSetting import *
from ComMonitor import *

CONNECT_CMD     = "5A 02 0D 01 0E CA"
DIS_CONNECT_CMD = "5A 02 CC 01 CF CA"
READ_UID_CMD    = "5A 03 55 49 44 5B CA"
SET_TAG_CMD     = "5A 09 06 0F 42 40 17 06 09 01 01 1A CA"

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = 'log.txt',
    filemode = 'w',
    format = u'【%(asctime)s】 %(message)s',
)

ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'

class CmdScript():
    def __init__(self, name, encode):
        self.name      = name
        self.encode    = encode
        self.cmds_list = []
        self.cmds_dict = {}
        self.time_dict = {}
        self.cmd_index = 0
        self.run_times = 0
        self.add_cmd("connect"    ,CONNECT_CMD    , 1  )
        self.add_cmd("dis_connect",DIS_CONNECT_CMD, 1  )
        self.add_cmd("read_uid"   ,READ_UID_CMD   , 0.1)
        self.add_cmd("set_tag"    ,SET_TAG_CMD    , 0.2)

    def add_cmd(self,name,value,timeout):
        self.cmds_list.append(name)
        self.cmds_dict[name] = value
        self.time_dict[name] = timeout

    def get_cmd(self):
        time_out  = self.time_dict[self.cmds_list[self.cmd_index]]
        cmd_value = self.cmds_dict[self.cmds_list[self.cmd_index]]
        self.cmd_index = self.cmd_index + 1
        # print time_out,cmd_value
        if self.cmd_index == len(self.cmds_list):
            self.cmd_index = 0
            return 0,""
        else:
            return time_out,cmd_value

    def change_cmd(self,cmd_name):
        print "change_cmd_name"

class DTQPutty(QMainWindow):
    def __init__(self, parent=None):
        super(DTQPutty, self).__init__(parent)
        self.process_bar   = 0
        self.monitor_dict  = {}
        self.com_dict      = {}
        self.com_edit_dict = {}
        self.window_dict   = {}
        self.mearge_flag   = 0
        self.script_list   = {}
        self.scripts_count = 0
        self.cur_script    = 0

        self.resize(700, 600)
        self.setWindowTitle(u'滤网RFID授权软件 V2.0')

        self.com_edit = QTextEdit()
        self.com_edit.setStyleSheet('QWidget {background-color:#111111}')
        self.com_edit.setFont(QFont("Courier New", 10, False))
        self.com_edit.setTextColor(QColor(200,200,200))

        self.led_item0 = QPushButton(u"串口1")
        self.led_item1 = QPushButton(u"串口2")
        self.led_item2 = QPushButton(u"串口3")
        self.led_item3 = QPushButton(u"串口4")
        l_vbox = QHBoxLayout()
        l_vbox.addWidget(self.led_item0)
        l_vbox.addWidget(self.led_item1)
        l_vbox.addWidget(self.led_item2)
        l_vbox.addWidget(self.led_item3)

        m_vbox = QVBoxLayout()
        m_vbox.addLayout(l_vbox)
        m_vbox.addWidget(self.com_edit)

        m_frame = QFrame()
        m_frame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        m_frame.setLayout(m_vbox)

        self.setCentralWidget(m_frame)
        self.com_edit.append("Open CONSOLE OK!")

        # get uart Config
        config = ConfigParser.ConfigParser()
        path = os.path.abspath("./")
        config.readfp(open(path + '\\data\\' + 'default_setting.inf', "rb"))
        file_num = config.get('script', 'file_num')

        self.statusBar()
        self.menubar = self.menuBar()
        # 设置
        self.exit = QAction('Exit', self)
        self.exit.setShortcut('Ctrl+Q')
        self.exit.setStatusTip(u'退出')
        self.new_session = QAction('New Session', self)
        self.new_session.setShortcut('Ctrl+O')
        self.new_session.setStatusTip(u'创建一个新的会话')
        self.connection = self.menubar.addMenu(u'&设置')
        self.connection.addAction(self.new_session)
        self.connection.addAction(self.exit)

        # 退出程序
        self.connect(self.exit, SIGNAL('triggered()'), SLOT('close()'))
        # 新的连接
        self.connect(self.new_session, SIGNAL('triggered()'), self.open_new_session)
        # 自动发送定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.uart_auto_send_script)

    def uart_auto_send_script(self):
        timeout,cmd_value = self.cur_script.get_cmd()
        if timeout != 0:
            self.timer.start(timeout*1000)

            for item in self.com_dict:
                self.monitor_dict[item].input_count = self.monitor_dict[item].input_count + 1
                index = u"<font color=lightgreen>S[%d]:</font>" % self.monitor_dict[item].input_count
                self.uart_update_text( item, index, cmd_value)
                logging.debug(u'发送数据:%s',cmd_value)

                if self.cur_script.encode == 'hex':
                    cmd_value = cmd_value.replace(' ','')
                    cmd_value = cmd_value.decode("hex")
                self.com_dict[item].write(cmd_value)
        else:
            self.timer.stop()

            for item in self.com_dict:
                self.monitor_dict[item].input_count = self.monitor_dict[item].input_count + 1
                index = u"<font color=lightgreen>S[%d]:</font>" % self.monitor_dict[item].input_count
                self.uart_update_text( item, index, u'脚本已经执行完毕...')

    def open_new_session(self):
        monitor = ComSetting.get_com_monitor()
        if monitor :
            # 创建监听线程
            self.monitor_dict[monitor.com.portstr] = monitor
            self.com_dict[monitor.com.portstr]     = monitor.com

            self.connect(self.monitor_dict[monitor.com.portstr],
                         SIGNAL('protocol_message(QString, QString)'),
                         self.update_edit)

            self.monitor_dict[monitor.com.portstr].start()
            logging.info(u"启动串口监听线程!")
            self.com_edit.append(u"启动串口 %s 监听线程!" % monitor.com.portstr )
        else:
            self.com_edit.append(u"Error:打开串口出错！")

    def add_script_fun1(self,file_path):
        # print file_path
        f = open(file_path,'rU')
        lines = f.readlines()
        f.close()

        for line_no in range(len(lines)):
            # print (line_no,lines[line_no][0:5])
            if lines[line_no][0:5] == u"[cmd]":
                start_line = line_no
                # print start_line
            if lines[line_no][0:5] == u"[enco":
                encode_style = lines[line_no+1]

        name = unicode(file_path.split("/")[-1])
        new_script = QTreeWidgetItem(self.tree_script)
        new_script.setText(0, name.split(".")[0] + "(%s)" % encode_style[0:3])

        self.script_list[self.scripts_count] = CmdScript(name, encode_style[0:3])
        self.script_list[self.scripts_count].encode = encode_style[0:3]

        cmds = lines[start_line+1:]

        for i in range(len(cmds)/2):
            item = cmds[i*2].strip('\n')
            item = unicode(item.decode('utf-8'))

            if item[0:1] == u"<":
                cmd_dsc = item[4:]
                timeout = string.atoi(item[1:3], 10)
            else:
               cmd_dsc = item[0:]
               timeout = 1
            #print cmd_dsc
            cmd = cmd_dsc.split(":")[0]

            self.script_list[self.scripts_count].add_cmd(cmd,cmds[i*2+1].strip('\n'),timeout)
            # print " index = %02d cmds = %s str_cmd = %s" % (i,cmd,self.json_cmd_dict[cmd])
            QTreeWidgetItem(new_script).setText(0, cmd)
        self.scripts_count = self.scripts_count + 1

    def add_script_fun(self):
        temp_image_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './', "txt files(*.inf)"))
        self.add_script_fun1(temp_image_path)

    def merge_display(self):
        if self.mearge_flag == 0:
            self.mearge_flag = 1
        else:
            self.mearge_flag = 0

    def update_edit(self,ser_str,data):
        index  = u"<font color=lightgreen>R[%d]:</font>" % self.monitor_dict[str(ser_str)].input_count
        self.uart_update_text(str(ser_str), index, data)

    def uart_update_text(self,ser_str,index,data):
        if self.mearge_flag == 0:
            ser = "CONSOLE"
        else:
            ser = str(ser_str)

        cursor = self.com_edit_dict[ser].textCursor()
        cursor.movePosition(QTextCursor.End)

        now = time.strftime( ISOTIMEFORMAT,time.localtime(time.time()))
        header = u"<font color=green>[%s]@%s:~$ </font>" % (now, ser_str)

        data = header + index + u"<font color=white>%s</font>" %  data

        if data[-1] == '%':
            if self.process_bar != 0:
                cursor.movePosition(QTextCursor.End,QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.StartOfLine,QTextCursor.KeepAnchor)
                cursor.selectedText()
                cursor.removeSelectedText()
                self.com_edit_dict[ser].setTextCursor(cursor)
                self.com_edit_dict[ser].insertPlainText(data)
            else:
                self.com_edit_dict[ser].setTextCursor(cursor)
                self.com_edit_dict[ser].append(data)
            self.process_bar = self.process_bar + 1
        else:
            self.com_edit_dict[ser].setTextCursor(cursor)
            self.com_edit_dict[ser].append(data)
        #print data

if __name__=='__main__':
    app = QApplication(sys.argv)
    datputty = DTQPutty()
    datputty.show()
    app.exec_()

