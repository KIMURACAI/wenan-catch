"""
统一异常定义

所有模块只能抛出这些异常。
"""
from typing import Optional


class AppError(Exception):
    """应用基础异常"""
    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause
        super().__init__(message)

    def __str__(self):
        if self.cause:
            return f"{self.message} ({type(self.cause).__name__}: {self.cause})"
        return self.message


class DownloadError(AppError):
    """视频下载失败"""
    pass


class ASRError(AppError):
    """语音转写失败"""
    pass


class AIError(AppError):
    """AI 润色失败"""
    pass


class FeishuError(AppError):
    """飞书 API 调用失败"""
    pass


class ConfigError(AppError):
    """配置错误"""
    pass


class BrowserError(AppError):
    """浏览器操作失败"""
    pass
