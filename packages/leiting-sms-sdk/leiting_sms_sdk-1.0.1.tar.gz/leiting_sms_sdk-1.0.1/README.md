# 雷霆短信验证码服务 Python SDK

[![PyPI version](https://badge.fury.io/py/leiting-sms-sdk.svg)](https://badge.fury.io/py/leiting-sms-sdk)
[![Python](https://img.shields.io/pypi/pyversions/leiting-sms-sdk.svg)](https://pypi.org/project/leiting-sms-sdk/)
[![License](https://img.shields.io/pypi/l/leiting-sms-sdk.svg)](https://github.com/yourusername/leiting-sms-sdk/blob/main/LICENSE)

雷霆短信验证码服务的Python SDK，提供简单易用的API接口，支持获取手机号、接收验证码等功能。

## 特性

- 🚀 简单易用的API接口
- 📱 支持多运营商手机号获取（移动、联通、电信）
- 🔄 自动线路切换，提高可用性
- 💰 余额查询功能
- 🛡️ 手机号管理（获取、释放、加黑）
- 📨 短信发送和接收
- 🎯 无异常处理设计，错误直接暴露便于调试

## 安装

```bash
pip install leiting-sms-sdk
```

## 快速开始

### 基本使用

```python
from leiting_sms_sdk import LeitingSMSClient

# 创建客户端（自动登录）
client = LeitingSMSClient(username="your_username", password="your_password")

# 查询余额
success, balance_info = client.get_balance()
if success:
    print(f"账户余额: {balance_info['balance']}")
    print(f"可提现余额: {balance_info['withdrawable']}")

# 获取手机号
success, phone = client.get_phone(project_id="your_project_id")
if success:
    print(f"获取到手机号: {phone}")
    
    # 获取验证码
    success, sms_content = client.get_sms(project_id="your_project_id", phone=phone)
    if success:
        print(f"收到短信: {sms_content}")
    
    # 释放手机号
    client.release_phone(project_id="your_project_id", phone=phone)
```

### 手动登录模式

```python
# 创建客户端但不自动登录
client = LeitingSMSClient(username="your_username", password="your_password", auto_login=False)

# 手动登录
success, token = client.login()
if success:
    print(f"登录成功，Token: {token}")
```

### 指定运营商获取手机号

```python
# 使用常量指定运营商
success, phone = client.get_phone(
    project_id="your_project_id",
    operator=LeitingSMSClient.OPERATOR_MOBILE  # 移动
)

# 或者直接使用数字
success, phone = client.get_phone(
    project_id="your_project_id",
    operator=1  # 1=移动, 2=联通, 3=电信, 0=默认
)
```

## API 参考

### LeitingSMSClient

#### 构造函数

```python
LeitingSMSClient(username: str, password: str, auto_login: bool = True)
```

- `username`: 用户名
- `password`: 密码  
- `auto_login`: 是否自动登录，默认True

#### 常量

```python
# 运营商常量
OPERATOR_DEFAULT = 0    # 默认
OPERATOR_MOBILE = 1     # 移动
OPERATOR_UNICOM = 2     # 联通
OPERATOR_TELECOM = 3    # 电信

# 卡类型常量
CARD_TYPE_DEFAULT = 0   # 默认
CARD_TYPE_VIRTUAL = 1   # 虚拟运营商
CARD_TYPE_PHYSICAL = 2  # 实卡运营商

# 过滤模式常量
FILTER_MODE_EXCLUDE_USED = 1  # 过滤已使用号码
FILTER_MODE_ALLOW_REUSE = 2   # 允许重复使用
```

#### 主要方法

##### login() -> Tuple[bool, str]
登录获取token
- 返回: (成功状态, token或错误信息)

##### get_balance() -> Tuple[bool, Union[dict, str]]
查询账户余额
- 返回: (成功状态, 余额信息字典或错误信息)

##### get_phone(project_id, operator=0, region="0", card=0, phone="", loop=1, filter_numbers="") -> Tuple[bool, str]
获取手机号码
- `project_id`: 项目ID
- `operator`: 运营商类型
- `region`: 地区（0=默认，或指定如"上海"）
- `card`: 卡类型
- `phone`: 指定号码（空则获取新号码）
- `loop`: 过滤模式
- `filter_numbers`: 排除号码段，如"165|170|"
- 返回: (成功状态, 手机号或错误信息)

##### get_sms(project_id, phone, developer_username=None) -> Tuple[bool, str]
获取验证码
- `project_id`: 项目ID
- `phone`: 手机号码
- `developer_username`: 开发者用户名（默认使用登录用户名）
- 返回: (成功状态, 短信内容或错误信息)

##### send_sms(project_id, phone, send_number, content) -> Tuple[bool, str]
发送短信
- `project_id`: 项目ID
- `phone`: 手机号码
- `send_number`: 发送号码（106开头）
- `content`: 发送内容（不支持中文）
- 返回: (成功状态, 结果信息或错误信息)

##### blacklist_phone(project_id, phone) -> Tuple[bool, str]
加黑手机号
- 返回: (成功状态, 结果信息或错误信息)

##### release_phone(project_id, phone) -> Tuple[bool, str]
释放手机号
- 返回: (成功状态, 结果信息或错误信息)

#### 辅助方法

##### is_ready() -> bool
检查客户端是否准备就绪（已登录且无错误）

##### get_last_error() -> Optional[str]
获取最后一次错误信息

## 便捷函数

```python
from leiting_sms_sdk import create_client

# 快速创建客户端
client = create_client("username", "password")
```

## 错误处理

本SDK采用返回值方式处理错误，不使用异常机制。所有API方法都返回 `(success, result)` 元组：

- `success`: bool类型，表示操作是否成功
- `result`: 成功时返回具体数据，失败时返回错误信息字符串

```python
success, result = client.get_phone("project_id")
if success:
    print(f"获取手机号成功: {result}")
else:
    print(f"获取手机号失败: {result}")
```

## 注意事项

1. **及时释放手机号**: 获取手机号后请及时释放，避免余额冻结
2. **API调用频率**: 获取验证码建议每5秒调用一次，避免触发限制
3. **线路切换**: SDK支持自动线路切换，提高服务可用性
4. **项目ID**: 请在雷霆短信客户端软件中查询您的项目ID

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持所有基础API功能
- 自动线路切换
- 完整的类型注解
