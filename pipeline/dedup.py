"""
去重引擎 - 避免重复采集和转录

策略:
1. post_id 主键去重（抖音 aweme_id 唯一）
2. content_hash 去重（检测作者删视频重发）
3. 增量采集（按发布时间停止滚动）
"""
import hashlib
import sqlite3
from datetime import datetime
from typing import Optional

from loguru import logger

from models.schemas import Post, TaskStatus
from storage.repository import Repository


class DedupEngine:
    """去重引擎"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def filter_new_posts(self, posts: list[Post]) -> tuple[list[Post], list[Post]]:
        """
        从采集到的视频中筛选出新视频

        Args:
            posts: 本次采集到的视频列表

        Returns:
            (new_posts, duplicate_posts)
        """
        if not posts:
            return [], []

        post_ids = [p.post_id for p in posts if p.post_id]
        existing_ids = Repository.find_existing_ids(self.conn, post_ids)

        new_posts = []
        duplicate_posts = []
        for post in posts:
            if post.post_id in existing_ids:
                duplicate_posts.append(post)
            else:
                new_posts.append(post)

        if duplicate_posts:
            logger.info(
                f"去重: {len(duplicate_posts)} 条已存在, "
                f"{len(new_posts)} 条新视频"
            )

        return new_posts, duplicate_posts

    def filter_new_by_hash(self, posts: list[Post]) -> list[Post]:
        """
        content_hash 去重（避免相同内容不同 ID 重复入库）
        对已有文案的视频，计算 desc hash 检查是否已存在。

        Returns:
            真正全新的视频列表
        """
        result = []
        for post in posts:
            if not post.video_desc:
                result.append(post)
                continue

            text_hash = self._hash_text(post.video_desc)
            cursor = self.conn.execute(
                "SELECT post_id FROM posts WHERE content_hash = ? LIMIT 1",
                (text_hash,),
            )
            if cursor.fetchone() is None:
                post.content_hash = text_hash
                result.append(post)
            else:
                logger.debug(f"content_hash 重复，跳过: {text_hash[:12]}")

        return result

    def get_unfinished(self, limit: int = 50) -> list[Post]:
        """获取所有未完成的视频（用于启动时继续处理）"""
        return Repository.find_unfinished_posts(self.conn, limit)

    def get_last_publish_time(self, target_name: str) -> Optional[datetime]:
        """
        获取某个目标的最新视频发布时间

        Returns:
            最新发布时间，None 表示从未采集过
        """
        cursor = self.conn.execute(
            """SELECT publish_time FROM posts
               WHERE source_target = ?
                 AND publish_time IS NOT NULL
               ORDER BY publish_time DESC LIMIT 1""",
            (target_name,),
        )
        row = cursor.fetchone()
        if row and row["publish_time"]:
            return datetime.fromisoformat(row["publish_time"])
        return None

    @staticmethod
    def _hash_text(text: str) -> str:
        """计算文本 SHA256 取前 32 位"""
        if not text:
            return ""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
