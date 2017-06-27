# ChangeLog:
*****************************************************************************************
* **版　　本：V0.1.0**
* **开发目的** 测试美的读头
* **特性描述** : 
	* 使用16进制的编码风格
*****************************************************************************************
* **时间**：2017-06-13
* **描述** :
> 1. 建立初版本，基本完成GUI的绘制

* **时间**：2017-06-14
* **描述** :
> 1. 修改面板，将操作和数据设置分块
> 2. 增加数据解析模块
> 3. 完善数据解析模块，完成16进制的协议解析
> 4. 串口发送数据模块的功能定义，基本完成数据交互
> 5. 修复数据解析模块CRC检验的BUG
> 6. 完成基本功能测试

* **时间**：2017-06-15
* **描述** :
> 1. 修复发送指令计数的BUG
> 2. 给指令的字体加上颜色使人易于区分
> 3. 增加按键之间的限制逻辑，没有打开串口不允许操作发送按钮
> 4. 修复接收数据不能超过10条的BUG
> 5. 增加对读取UID功能指令的限制
> 6. 打印指令CRC总是为0的BUG

*****************************************************************************************
* **版　　本：V0.2.0**
* **开发目的** : 使用新的协议与方案
* **特性描述** : 
	* 使用新的协议，使之同时支持4路串口同时操作
*****************************************************************************************
* **时间**：2017-06-19
* **描述** :
> 1. 基本完成了协议框架的搭建，支持点击配置界面的出现
> 2. 修改配置界面，完成指令逻辑的定义

* **时间**：2017-06-23
* **描述** :
> 1. 基本完成了开始界面的设计
> 2. 基本完成软件框架的搭建

* **时间**：2017-06-24
* **描述** :
> 1. 完成LED只是灯类的封装
> 2. 完成初始界面按键逻辑的定义
> 3. 完成工人界面的定义
> 4. 整理工程文件，剔除无用的文件
> 5. 重构串口配置界面的逻辑之整理，实现配置界面与数据的分离
> 6. 完成指令的解析与L4路串口逻辑的分离

* **时间**：2017-06-26
* **描述** :
> 1. 完成设置界面与生产界面的LED状态同步
> 2. 修改配置界面数据同步方式，将数据同步到配置文件中
> 3. 完成部分SN配置信息的同步

* **时间**：2017-06-27
* **描述** :
> 1. 完成SN配置信息的同步
> 2. 修复滤网配置信息错位的BUG
> 3. 完成SN配置界面的分离，实现管理员界面与工人界面与逻辑的复用
