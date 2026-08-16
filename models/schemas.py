"""
数据模型定义

核心模型:
- Post: 单条视频数据（含文案和处理状态）
- ScrapeTarget: 采集目标（用户或话题）
- DailyReport: 日报元数据
- RunLog: 运行日志
"""
from collections import Counter
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TargetType(str, Enum):
    """目标类型"""
    USER = "user"
    HASHTAG = "hashtag"


class TargetStatus(str, Enum):
    """目标状态"""
    ACTIVE = "active"
    PAUSED = "paused"


class TaskStatus(str, Enum):
    """
    任务状态机 - 每条视频的处理状态

    流转:
        NEW -> DOWNLOADED -> ASR_OK -> AI_OK -> DONE
        |        |           |         |
        +-> FAILED  +-> FAILED  +-> FAILED  +-> FAILED
    """
    NEW = "new"                    # 新采集，待处理
    DOWNLOADING = "downloading"    # 下载中
    DOWNLOADED = "downloaded"      # 视频已下载
    ASR_PENDING = "asr_pending"   # ASR 处理中
    ASR_OK = "asr_ok"             # ASR 转写完成
    AI_PENDING = "ai_pending"     # AI 润色中
    AI_OK = "ai_ok"               # AI 润色完成
    DONE = "done"                 # 全部完成
    FAILED = "failed"             # 处理失败


class ScrapeTarget(BaseModel):
    """采集目标 - 一个抖音用户或话题"""
    name: str
    target_type: TargetType
    douyin_id: str                # 用户: sec_uid, 话题: hashtag_id
    status: TargetStatus = TargetStatus.ACTIVE
    notes: str = ""


class Post(BaseModel):
    """单条抖音视频数据"""
    # ── 唯一标识 ──
    post_id: str                  # aweme_id，抖音视频唯一ID
    video_url: str = ""           # 视频链接（主要）
    video_urls: list[str] = Field(default_factory=list)  # 所有可用的播放地址

    # ── 作者信息 ──
    author_name: str = ""
    author_id: str = ""

    # ── 页面文案 ──
    video_desc: str = ""          # 视频描述/文案（页面已有的文字）
    video_title: str = ""         # 视频标题

    # ── ASR 转写结果 ──
    transcribed_text: str = ""    # 火山引擎 ASR 转写（已精炼）
    transcribed_text_raw: str = ""  # ASR 原始转写

    # ── AI 润色结果 ──
    ai_refined_text: str = ""     # AI 润色后的文案

    # ── 任务状态 ──
    task_status: TaskStatus = TaskStatus.NEW
    retry_count: int = 0           # 重试次数
    error_msg: str = ""            # 最后的错误信息

    # ── 时间信息 ──
    publish_time: Optional[datetime] = None
    collected_at: datetime = Field(default_factory=datetime.now)

    # ── 元信息 ──
    hashtags: list[str] = Field(default_factory=list)
    source_target: str = ""       # 来自哪个目标
    source_type: TargetType = TargetType.USER

    # ── 去重 ──
    content_hash: str = ""         # 转写文本的 hash，检测重发

    # ── Content Engine ──
    content_type: str = ""               # 分类结果（如"道家智慧"）
    content_type_confidence: float = 0.0
    quality_score: float = 0.0           # 质量总分（0-100）
    quality_dimensions: str = ""         # JSON: 各维度得分
    template_used: str = ""              # 使用的模板名
    regenerated: bool = False            # 是否触发过重写

    @property
    def final_copy(self) -> str:
        """
        最终文案（优先级）:
        1. AI 润色文本（AI_OK 时优先）
        2. ASR 转写文本（非空且非乱码）
        3. 页面文案（video_desc）
        4. 标题
        """
        if self.ai_refined_text and self.task_status == TaskStatus.AI_OK:
            return self.ai_refined_text
        if self.transcribed_text and not self._text_is_garbled(self.transcribed_text):
            return self.transcribed_text
        if self.video_desc:
            return self.video_desc
        return self.video_title

    @staticmethod
    def _text_is_garbled(text: str) -> bool:
        """检测文本是否为乱码/无意义"""
        if not text or len(text.strip()) < 3:
            return True
        chinese = sum(1 for c in text if '一' <= c <= '鿿')
        total = len(text.strip().replace(' ', ''))
        if total > 0 and chinese / total < 0.5:
            return True
        # 重复检测
        if len(text) >= 8:
            for w in [2, 3]:
                counts = Counter(text[i:i+w] for i in range(len(text)-w+1))
                if any(c >= 4 for c in counts.values()):
                    return True
        return False

    @property
    def clean_copy(self) -> str:
        """
        适合口播的干净文案

        如果 desc 是纯标签（#书法#国画），说明没有真实文案，
        返回空字符串。

        如果有真实文案:
        - 去除 URL
        - 去除多余空白和换行
        - 确保以句号结尾
        """
        import re
        text = self.final_copy

        # 检查是否只有标签/链接/乱码，没有真实文案
        cleaned_check = re.sub(r'#\S+|@\S+|https?://\S+', '', text).strip()
        cleaned_check = cleaned_check.strip('#@，。！？：；,.:;!? ')
        if len(cleaned_check) < 4:
            return ""
        if self._text_is_garbled(cleaned_check):
            return ""

        # 有真实文案，做清洗
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'#\S+', '', text)
        # 保留段落结构
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        text = '\n'.join(paragraphs)
        # 确保每段以句号结尾
        paragraphs = text.split('\n')
        for i, p in enumerate(paragraphs):
            p = p.strip()
            if p and p[-1] not in '。！？，：':
                p += '。'
            paragraphs[i] = p
        text = '\n'.join(paragraphs)

        return text

    @property
    def has_audio_transcript(self) -> bool:
        """是否已通过语音转文字获取了文案"""
        return bool(self.transcribed_text) and self.task_status in (
            TaskStatus.ASR_OK, TaskStatus.AI_OK, TaskStatus.DONE)


class DailyReport(BaseModel):
    """日报元数据"""
    date: str                      # "2026-07-09"
    doc_token: Optional[str] = None  # 飞书文档 token
    doc_url: Optional[str] = None
    post_count: int = 0
    target_count: int = 0
    transcribed_count: int = 0     # 其中转录了多少条
    created_at: datetime = Field(default_factory=datetime.now)


class RunLog(BaseModel):
    """运行日志记录"""
    run_date: str                  # "2026-07-09"
    started_at: datetime
    finished_at: Optional[datetime] = None
    targets_count: int = 0
    posts_collected: int = 0
    posts_new: int = 0
    posts_duplicate: int = 0
    posts_transcribed: int = 0
    status: str = "running"        # running | success | failed
    error_message: str = ""
