"""
飞书文档内容构建器 - 单条文案格式

每个账号一个文档，每次追加新条目。

条目格式:
--------------------------------
采集时间：
视频标题：
视频链接：
原始ASR：
整理后文案：
--------------------------------
"""
from datetime import datetime
from models.schemas import Post, TargetType


class DocumentBuilder:
    """文案条目构建器"""

    BLOCK_TYPE_TEXT = 2
    BLOCK_TYPE_DIVIDER = 22

    @staticmethod
    def build_entry_blocks(posts: list[Post], target_name: str) -> list[dict]:
        """构建单条文案的 blocks（一个目标的所有新文案）"""
        blocks = []

        for post in posts:
            # 分隔线
            blocks.append(DocumentBuilder._divider())

            # 采集时间
            collected = post.collected_at.strftime("%Y-%m-%d %H:%M")
            blocks.append(DocumentBuilder._text(f"采集时间：{collected}"))

            # 视频标题
            if post.video_title:
                blocks.append(DocumentBuilder._text(f"视频标题：{post.video_title}"))

            # ASR 原文
            if post.transcribed_text:
                blocks.append(DocumentBuilder._text(""))
                blocks.append(DocumentBuilder._text("【原始ASR】"))
                blocks.append(DocumentBuilder._text(post.transcribed_text))

            # 整理后文案
            final = post.ai_refined_text or post.transcribed_text or post.video_desc or post.video_title
            if final:
                blocks.append(DocumentBuilder._text(""))
                blocks.append(DocumentBuilder._text("【整理后文案】"))
                blocks.append(DocumentBuilder._text(final))

            blocks.append(DocumentBuilder._text(""))

        return blocks

    @staticmethod
    def _text(content: str) -> dict:
        return {
            "block_type": DocumentBuilder.BLOCK_TYPE_TEXT,
            "text": {
                "elements": [{"text_run": {"content": content, "text_element_style": {}}}],
                "style": {},
            },
        }

    @staticmethod
    def _divider() -> dict:
        return {
            "block_type": DocumentBuilder.BLOCK_TYPE_DIVIDER,
            "divider": {},
        }
