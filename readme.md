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
> 4. 完成设置界面的TAG模块的分离
> 5. 修改SN配置界面，将SN序列号放到最下面
> 6. 修改TAG界面，选择串口增加互斥逻辑，2个标签不能绑定到同一个串口
> 7. 修复选择串口下拉列表出重复出现COM的BUG
> 8. 完成读卡指令的功能
> 9. 完成LED对结果的显示逻辑

* **时间**: 2017-06-28
* **描述**:
> 1. 完成简单的发送指令的逻辑
> 2. 完成简单的发卡逻辑

*****************************************************************************************
* **版　　本：V0.2.1**
* **开发目的** : 去美的对接之后的修改版本
* **特性描述** :
	* 串口自动选择和连接
*****************************************************************************************
* **时间**: 2017-06-30
* **描述**:
> 1. 创建新的分支，自动完成设备搜索
> 2. 完成新协议的修改，增加CCM及预留字段

* **时间**: 2017-07-01
* **描述**:
> 1. 修复搜索串口设备时发送链接设备指令一直等待，导致程序卡死的BUG
> 2. 优化发送指令状态机，支持空闲无卡状态的显示，与打印信息的输出
> 3. 完成有无标签的识别功能，并在LED等上显示，避免重复烧录
> 4. 完成烧录完成之后，寻卡会偶尔失败显现的过滤
> 5. 完成配置界面与工作界面的关联剥离，2个界面都可以重复打开设置
> 6. 修复配置文件部分值为空时，配置界面无法出现的BUG

* **时间**: 2017-07-02
* **描述**:
> 1. 增加对PC端不接设备的异常处理

* **时间**: 2017-07-02
* **描述**:
> 1. 增加绑定串口与标签显示
> 2. 完成txt格式的LOG日志的输出
> 3. 完成软件关闭时SN序列号的保存逻辑
> 4. 将产线号按要求修改为下拉列表的形式
> 5. 完成工人界面的下拉列表的限制逻辑
> 6. 优化打印输出代码
> 7. 增加发卡成功时的蜂鸣器鸣叫逻辑
