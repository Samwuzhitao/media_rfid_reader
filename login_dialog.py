# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
import sys

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(u'登录')
            # self.resize(300,150)
        self.sw_label   = QLabel(u"滤网RFID标签授权")
        self.sw_label.setFont(QFont("Roman times",40,QFont.Bold))
        self.sw_label.setAlignment(Qt.AlignCenter)
        self.zkxl_label = QLabel(u"版权所有：深圳中科讯联科技有限公司")
        self.zkxl_label.setFont(QFont("Roman times",20,QFont.Bold))
        self.zkxl_label.setAlignment(Qt.AlignCenter)
        self.leName =QLineEdit(u'admin')
        self.leName.setPlaceholderText(u'用户名')

        self.lePassword =QLineEdit(self)
        self.lePassword.setEchoMode(QLineEdit.Password)
        self.lePassword.setPlaceholderText(u'密码')

        self.pbLogin  = QPushButton(u'登录',self)
        self.pbCancel = QPushButton(u'取消',self)
        # self.pbLogin.setFixedSize(200, 40)
        # self.pbCancel.setFixedSize(200, 40)
        self.pbLogin.clicked.connect(self.login)
        self.pbCancel.clicked.connect(self.reject)
        buttonLayout = QHBoxLayout()
        buttonLayout.addItem(QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        buttonLayout.addWidget(self.pbLogin)
        buttonLayout.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        buttonLayout.addWidget(self.pbCancel)

        layout =QVBoxLayout()
        # layout.addWidget(self.sw_label)
        layout.addWidget(self.leName)
        layout.addWidget(self.lePassword)
        layout.addLayout(buttonLayout)
        # layout.addWidget(self.zkxl_label)

        self.setLayout(layout)

    def login(self):
        print'login'
        if self.leName.text()=='admin' and self.lePassword.text()=='zkxl':
            self.accept()# 关闭对话框并返回1
        else:
            QMessageBox.critical(self, u'错误', u'用户名密码不匹配')
