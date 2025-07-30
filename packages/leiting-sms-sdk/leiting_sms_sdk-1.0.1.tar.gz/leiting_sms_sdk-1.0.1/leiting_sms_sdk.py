"""
雷霆短信验证码服务 Python SDK

支持功能：
- 登录获取token
- 查询余额
- 获取手机号码
- 获取验证码
- 发短信上传
- 加黑手机号
- 释放手机号

使用示例：
    client = LeitingSMSClient(username="your_username", password="your_password")

    # 登录
    success, token = client.login()

    # 查询余额
    success, balance_info = client.get_balance()

    # 获取手机号
    success, phone = client.get_phone(project_id="123")

    # 获取验证码
    success, sms_content = client.get_sms(project_id="123", phone="13800138000")

编码规范：
- 不使用异常处理，让错误直接暴露便于调试
- 使用返回值方式处理错误状态
"""

import requests
import urllib.parse
from typing import List, Optional, Tuple, Union

__version__ = "1.0.1"
__author__ = "Your Name"
__email__ = "your.email@example.com"


class LeitingSMSClient:
    """雷霆短信验证码服务客户端"""

    # API配置常量
    API_HOSTS: List[str] = [
        "api.aomoton.com",
        "api.leiting888.xyz"
    ]

    API_PORT: int = 8000
    API_PROTOCOL: str = "http"
    REQUEST_TIMEOUT: int = 30

    # 运营商常量
    OPERATOR_DEFAULT: int = 0
    OPERATOR_MOBILE: int = 1
    OPERATOR_UNICOM: int = 2
    OPERATOR_TELECOM: int = 3

    # 卡类型常量
    CARD_TYPE_DEFAULT: int = 0
    CARD_TYPE_VIRTUAL: int = 1
    CARD_TYPE_PHYSICAL: int = 2

    # 过滤模式常量
    FILTER_MODE_EXCLUDE_USED: int = 1
    FILTER_MODE_ALLOW_REUSE: int = 2
    
    def __init__(self, username: str, password: str, auto_login: bool = True):
        """
        初始化客户端

        Args:
            username: 用户名
            password: 密码
            auto_login: 是否自动登录获取token
        """
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.current_host_index = 0
        self.last_error: Optional[str] = None

        if auto_login:
            success, result = self.login()
            if not success:
                self.last_error = f"自动登录失败: {result}"
    
    def _get_current_host(self) -> str:
        """获取当前使用的API主机"""
        return self.API_HOSTS[self.current_host_index]
    
    def _switch_host(self) -> None:
        """切换到下一个API主机"""
        self.current_host_index = (self.current_host_index + 1) % len(self.API_HOSTS)

    def is_ready(self) -> bool:
        """检查客户端是否准备就绪（已登录且无错误）"""
        return self.token is not None and self.last_error is None

    def get_last_error(self) -> Optional[str]:
        """获取最后一次错误信息"""
        return self.last_error
    
    def _make_request(self, endpoint: str, params: dict, retry_on_failure: bool = True) -> Tuple[bool, str]:
        """
        发起API请求

        Args:
            endpoint: API端点
            params: 请求参数
            retry_on_failure: 失败时是否尝试切换线路重试

        Returns:
            (success, response_data)
        """
        # 构建URL
        host = self._get_current_host()
        base_url = f"{self.API_PROTOCOL}://{host}:{self.API_PORT}/api/{endpoint}"

        # 编码参数 - 使用标准URL参数格式
        query_string = "&".join([
            f"{k}={urllib.parse.quote(str(v))}"
            for k, v in params.items()
            if v is not None and str(v) != ""
        ])
        full_url = f"{base_url}/{query_string}" if query_string else base_url

        # 发起HTTP请求
        response = requests.get(full_url, timeout=self.REQUEST_TIMEOUT)

        # 检查HTTP状态码
        if response.status_code != 200:
            error_msg = f"HTTP错误: {response.status_code} - {response.text}"
            if retry_on_failure and self.current_host_index < len(self.API_HOSTS) - 1:
                self._switch_host()
                return self._make_request(endpoint, params, False)
            return False, error_msg

        # 解析响应内容 - 使用GBK编码
        response.encoding = 'gbk'
        content = response.text.strip()
        if content.startswith("1|"):
            return True, content[2:]  # 成功，返回数据部分
        elif content.startswith("0|"):
            return False, content[2:]  # 失败，返回错误信息
        else:
            return False, f"未知响应格式: {content}"
                
    
    def login(self) -> Tuple[bool, str]:
        """
        登录获取token
        
        Returns:
            (success, token_or_error_message)
        """
        params = {
            "username": self.username,
            "password": self.password
        }
        
        success, result = self._make_request("sign", params)
        if success:
            self.token = result
            return True, result
        else:
            return False, result
    
    def get_balance(self) -> Tuple[bool, Union[dict, str]]:
        """
        查询余额

        Returns:
            (success, balance_info_or_error_message)
            balance_info格式: {"balance": "余额", "withdrawable": "可提现余额"}
        """
        if not self.token:
            return False, "未登录，请先调用login()方法"

        params = {"token": self.token}
        success, result = self._make_request("yh_gx", params)

        if success:
            # 解析余额信息: "余额|可提现余额" 或 "余额|1|可提现余额"
            parts = result.split("|")
            if len(parts) >= 2:
                if len(parts) == 2:
                    balance, withdrawable = parts
                else:  # len(parts) == 3, 中间是状态码
                    balance, _, withdrawable = parts

                return True, {
                    "balance": balance,
                    "withdrawable": withdrawable
                }
            else:
                return False, f"余额信息格式错误: {result}"
        else:
            return False, result
    
    def get_phone(self,
                  project_id: str,
                  operator: int = OPERATOR_DEFAULT,
                  region: str = "0",
                  card: int = CARD_TYPE_DEFAULT,
                  phone: str = "",
                  loop: int = FILTER_MODE_EXCLUDE_USED,
                  filter_numbers: str = "") -> Tuple[bool, str]:
        """
        获取手机号码

        Args:
            project_id: 项目ID
            operator: 运营商 (0=默认 1=移动 2=联通 3=电信)
            region: 地区 (0=默认，或指定地区如"上海")
            card: 卡类型 (0=默认 1=虚拟运营商 2=实卡运营商)
            phone: 指定获取的号码（为空则获取新号码）
            loop: 过滤模式 (1=过滤已做过号码 2=不过滤可循环获取)
            filter_numbers: 排除号码段，如"165|170|"

        Returns:
            (success, phone_number_or_error_message)
        """
        if not self.token:
            return False, "未登录，请先调用login()方法"

        params = {
            "id": project_id,
            "operator": operator,
            "Region": region,  # 注意：API要求大写R
            "card": card,
            "phone": phone,
            "loop": loop,
            "filer": filter_numbers,  # 注意：API参数名是filer不是filter
            "token": self.token
        }

        return self._make_request("yh_qh", params)
    
    def get_sms(self,
                project_id: str,
                phone: str,
                developer_username: Optional[str] = None) -> Tuple[bool, str]:
        """
        获取验证码

        Args:
            project_id: 项目ID
            phone: 手机号码
            developer_username: 开发者用户名（默认使用登录用户名）

        Returns:
            (success, sms_content_or_error_message)
        """
        if not self.token:
            return False, "未登录，请先调用login()方法"

        params = {
            "id": project_id,
            "phone": phone,
            "t": developer_username or self.username,
            "token": self.token
        }

        return self._make_request("yh_qm", params)
    
    def send_sms(self,
                 project_id: str,
                 phone: str,
                 send_number: str,
                 content: str) -> Tuple[bool, str]:
        """
        发短信上传

        Args:
            project_id: 项目ID
            phone: 手机号码
            send_number: 发送号码（只能发送106开头的服务短信）
            content: 发送内容（不能发送中文）

        Returns:
            (success, result_message_or_error_message)
        """
        if not self.token:
            return False, "未登录，请先调用login()方法"

        params = {
            "id": project_id,
            "phone": phone,
            "send": send_number,
            "content": content,
            "token": self.token
        }

        return self._make_request("fdx_tj", params)
    
    def blacklist_phone(self, project_id: str, phone: str) -> Tuple[bool, str]:
        """
        加黑手机号

        Args:
            project_id: 项目ID
            phone: 手机号码

        Returns:
            (success, result_message_or_error_message)
        """
        if not self.token:
            return False, "未登录，请先调用login()方法"

        params = {
            "id": project_id,
            "phone": phone,
            "token": self.token
        }

        return self._make_request("yh_lh", params)

    def release_phone(self, project_id: str, phone: str) -> Tuple[bool, str]:
        """
        释放手机号

        Args:
            project_id: 项目ID
            phone: 手机号码

        Returns:
            (success, result_message_or_error_message)
        """
        if not self.token:
            return False, "未登录，请先调用login()方法"

        params = {
            "id": project_id,
            "phone": phone,
            "token": self.token
        }

        return self._make_request("yh_sf", params)


# 便捷函数
def create_client(username: str, password: str, auto_login: bool = True) -> LeitingSMSClient:
    """创建雷霆短信客户端实例"""
    return LeitingSMSClient(username, password, auto_login)


if __name__ == "__main__":
    # 使用示例
    print("雷霆短信验证码服务 Python SDK")
    print("使用示例请参考类文档和方法注释")
