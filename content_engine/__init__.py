"""
Content Engine - 传统文化短视频内容生产引擎

将 ASR 转写文本升级为符合账号定位、自然流畅、
具有传统文化韵味、适合短视频口播的高质量文案。
"""
from .pipeline import ContentEnginePipeline, ContentEngineResult

__all__ = ["ContentEnginePipeline", "ContentEngineResult"]
