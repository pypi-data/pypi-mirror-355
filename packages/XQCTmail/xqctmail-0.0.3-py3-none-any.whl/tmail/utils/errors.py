"""
作者：Xiaoqiang
微信公众号：XiaoqiangClub
创建时间：2025/6/9 20:17
文件描述：错误
文件路径：src/tmail/utils/errors.py
"""

class BaseError(Exception):
    default_message = "🚨 默认错误消息！"  # 默认消息

    def __init__(self, message=None):
        self.message = message or self.default_message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class NoEmailError(BaseError):
    """
    没有设置邮箱的错误类
    """
    default_message = "🚨 请先调用 set_email() 设置邮箱后，并调用 enter_email() 进入邮箱！"


class AttachError(BaseError):
    """
    浏览器连接错误
    """
    default_message = "🚨 浏览器接管失败！"


class FinishError(BaseError):
    """
    浏览器结束错误
    """
    default_message = "🚨 浏览器关闭清理失败！"


class InteractiveError(BaseError):
    """
    浏览器交互错误
    """
    default_message = "🚨 交互错误！"


class UserAuthenticationError(BaseError):
    """
    用户认证错误
    """
    default_message = "🚨 用户认证失败！关注微信公众号：XiaoqiangClub，发送：用户认证，可获取最新 Token"
