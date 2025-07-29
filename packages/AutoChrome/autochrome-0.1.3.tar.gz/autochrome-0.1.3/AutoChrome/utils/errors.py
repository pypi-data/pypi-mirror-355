"""
作者：Xiaoqiang
微信公众号：XiaoqiangClub
创建时间：2025/6/14 08:13
文件描述：错误
文件路径：AutoChrome/utils/errors.py
"""


class ErrorBase(Exception):
    """
    错误基类
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class NotFoundChromeError(ErrorBase):
    """
    未找到chrome浏览器
    """

    def __init__(self, message="🚨 未找到chrome浏览器"):
        super().__init__(message)
