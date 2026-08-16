"""
数据仓库 - 统一的 CRUD 操作层

所有数据库操作只能经过 Repository。
禁止业务层直接写 SQL。
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional

from models.schemas import (
    Post, RunLog, ScrapeTarget,
    TargetType, TargetStatus, TaskStatus,
)


class Repository:
    """数据仓库 —— 唯一数据库操作入口"""

    # ═══════════════════════════════════════════
    # Posts - 写入
    # ═══════════════════════════════════════════

    @staticmethod
    def save_posts(conn: sqlite3.Connection, posts: list[Post]):
        """批量保存新视频（INSERT OR IGNORE）"""
        conn.executemany(
            """INSERT OR IGNORE INTO posts
               (post_id, author_name, author_id, video_title, video_desc,
                transcribed_text, transcribed_text_raw, ai_refined_text,
                task_status, retry_count, error_msg, content_hash,
                content_type, content_type_confidence, quality_score, quality_dimensions,
                template_used, regenerated,
                publish_time, collected_at, video_url, hashtags,
                source_target, source_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    p.post_id, p.author_name, p.author_id,
                    p.video_title, p.video_desc,
                    p.transcribed_text, p.transcribed_text_raw, p.ai_refined_text,
                    p.task_status.value, p.retry_count, p.error_msg, p.content_hash,
                    p.content_type, p.content_type_confidence,
                    p.quality_score, p.quality_dimensions,
                    p.template_used, int(p.regenerated),
                    p.publish_time.isoformat() if p.publish_time else None,
                    p.collected_at.isoformat(),
                    p.video_url,
                    json.dumps(p.hashtags, ensure_ascii=False),
                    p.source_target, p.source_type.value,
                )
                for p in posts
            ],
        )
        conn.commit()

    @staticmethod
    def update_post_status(
        conn: sqlite3.Connection,
        post_id: str,
        task_status: TaskStatus,
        error_msg: str = "",
    ):
        """更新任务状态"""
        conn.execute(
            """UPDATE posts
               SET task_status = ?, error_msg = ?
               WHERE post_id = ?""",
            (task_status.value, error_msg, post_id),
        )
        conn.commit()

    @staticmethod
    def update_transcription(
        conn: sqlite3.Connection,
        post_id: str,
        transcribed_text: str,
        transcribed_text_raw: str = "",
        task_status: TaskStatus = TaskStatus.ASR_OK,
    ):
        """更新 ASR 转写结果"""
        conn.execute(
            """UPDATE posts
               SET transcribed_text = ?,
                   transcribed_text_raw = ?,
                   task_status = ?,
                   error_msg = ''
               WHERE post_id = ?""",
            (transcribed_text, transcribed_text_raw, task_status.value, post_id),
        )
        conn.commit()

    @staticmethod
    def update_ai_refined(
        conn: sqlite3.Connection,
        post_id: str,
        ai_refined_text: str,
        task_status: TaskStatus = TaskStatus.AI_OK,
    ):
        """更新 AI 润色结果"""
        conn.execute(
            """UPDATE posts
               SET ai_refined_text = ?, task_status = ?
               WHERE post_id = ?""",
            (ai_refined_text, task_status.value, post_id),
        )
        conn.commit()

    @staticmethod
    def increment_retry(
        conn: sqlite3.Connection,
        post_id: str,
        error_msg: str = "",
        max_retries: int = 3,
    ):
        """递增重试计数，超过上限则标记 FAILED"""
        cur = conn.execute(
            "SELECT retry_count FROM posts WHERE post_id = ?", (post_id,)
        )
        row = cur.fetchone()
        current = (row["retry_count"] if row else 0) + 1
        status = TaskStatus.FAILED if current >= max_retries else TaskStatus.NEW
        conn.execute(
            """UPDATE posts
               SET retry_count = ?, task_status = ?, error_msg = ?
               WHERE post_id = ?""",
            (current, status.value, error_msg, post_id),
        )
        conn.commit()

    @staticmethod
    def update_content_engine_results(
        conn: sqlite3.Connection,
        post_id: str,
        ai_refined_text: str,
        content_type: str = "",
        content_type_confidence: float = 0.0,
        quality_score: float = 0.0,
        quality_dimensions: str = "",
        template_used: str = "",
        regenerated: bool = False,
        task_status: TaskStatus = TaskStatus.AI_OK,
    ):
        """更新 Content Engine 全部结果"""
        conn.execute(
            """UPDATE posts SET
               ai_refined_text = ?, task_status = ?,
               content_type = ?, content_type_confidence = ?,
               quality_score = ?, quality_dimensions = ?,
               template_used = ?, regenerated = ?
               WHERE post_id = ?""",
            (
                ai_refined_text, task_status.value,
                content_type, content_type_confidence,
                quality_score, quality_dimensions,
                template_used, int(regenerated),
                post_id,
            ),
        )
        conn.commit()

    @staticmethod
    def mark_done(conn: sqlite3.Connection, post_id: str):
        """标记为完成"""
        conn.execute(
            "UPDATE posts SET task_status = ?, error_msg = '' WHERE post_id = ?",
            (TaskStatus.DONE.value, post_id),
        )
        conn.commit()

    # ═══════════════════════════════════════════
    # Posts - 查询
    # ═══════════════════════════════════════════

    @staticmethod
    def find_existing_ids(conn: sqlite3.Connection, post_ids: list[str]) -> set[str]:
        """批量查询已存在的 post_id"""
        if not post_ids:
            return set()
        placeholders = ",".join("?" for _ in post_ids)
        cursor = conn.execute(
            f"SELECT post_id FROM posts WHERE post_id IN ({placeholders})",
            post_ids,
        )
        return {row["post_id"] for row in cursor.fetchall()}

    @staticmethod
    def find_posts_needing_download(
        conn: sqlite3.Connection, limit: int = 30,
    ) -> list[Post]:
        """查询需要下载的视频（task_status = NEW）"""
        cursor = conn.execute(
            """SELECT * FROM posts
               WHERE task_status = 'new'
               ORDER BY collected_at ASC
               LIMIT ?""",
            (limit,),
        )
        return [Repository._row_to_post(row) for row in cursor.fetchall()]

    @staticmethod
    def find_posts_needing_asr(
        conn: sqlite3.Connection, limit: int = 20,
    ) -> list[Post]:
        """查询需要 ASR 转写的视频"""
        cursor = conn.execute(
            """SELECT * FROM posts
               WHERE task_status = 'downloaded'
               ORDER BY collected_at ASC
               LIMIT ?""",
            (limit,),
        )
        return [Repository._row_to_post(row) for row in cursor.fetchall()]

    @staticmethod
    def find_posts_needing_ai(
        conn: sqlite3.Connection, limit: int = 20,
    ) -> list[Post]:
        """查询需要 AI 润色的视频"""
        cursor = conn.execute(
            """SELECT * FROM posts
               WHERE task_status = 'asr_ok'
               ORDER BY collected_at ASC
               LIMIT ?""",
            (limit,),
        )
        return [Repository._row_to_post(row) for row in cursor.fetchall()]

    @staticmethod
    def find_unfinished_posts(
        conn: sqlite3.Connection, limit: int = 50,
    ) -> list[Post]:
        """
        查询未完成的视频（用于启动时继续处理）
        排除: done, failed
        """
        cursor = conn.execute(
            """SELECT * FROM posts
               WHERE task_status NOT IN ('done', 'failed')
               ORDER BY collected_at ASC
               LIMIT ?""",
            (limit,),
        )
        return [Repository._row_to_post(row) for row in cursor.fetchall()]

    @staticmethod
    def get_recent_posts(
        conn: sqlite3.Connection, since: datetime, limit: int = 100,
    ) -> list[Post]:
        """查询指定时间后的视频（用于生成日报）"""
        cursor = conn.execute(
            """SELECT * FROM posts
               WHERE collected_at >= ?
               ORDER BY source_target, publish_time DESC
               LIMIT ?""",
            (since.isoformat(), limit),
        )
        return [Repository._row_to_post(row) for row in cursor.fetchall()]

    @staticmethod
    def get_post(conn: sqlite3.Connection, post_id: str) -> Optional[Post]:
        """按 post_id 查询单条视频"""
        cursor = conn.execute(
            "SELECT * FROM posts WHERE post_id = ?", (post_id,)
        )
        row = cursor.fetchone()
        return Repository._row_to_post(row) if row else None

    @staticmethod
    def get_post_count(conn: sqlite3.Connection) -> int:
        """获取总视频数"""
        row = conn.execute("SELECT COUNT(*) AS cnt FROM posts").fetchone()
        return row["cnt"] if row else 0

    # ═══════════════════════════════════════════
    # Run Logs
    # ═══════════════════════════════════════════

    @staticmethod
    def create_run_log(conn: sqlite3.Connection, run_log: RunLog) -> int:
        """创建运行日志，返回 ID"""
        cursor = conn.execute(
            """INSERT INTO run_logs
               (run_date, started_at, targets_count, status)
               VALUES (?, ?, ?, ?)""",
            (run_log.run_date, run_log.started_at.isoformat(),
             run_log.targets_count, run_log.status),
        )
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def complete_run_log(
        conn: sqlite3.Connection,
        log_id: int,
        posts_collected: int,
        posts_new: int,
        posts_duplicate: int,
        posts_transcribed: int,
        status: str,
        error_message: str = "",
    ):
        """完成运行日志"""
        conn.execute(
            """UPDATE run_logs SET
               finished_at = ?,
               posts_collected = ?,
               posts_new = ?,
               posts_duplicate = ?,
               posts_transcribed = ?,
               status = ?,
               error_message = ?
               WHERE id = ?""",
            (
                datetime.now().isoformat(),
                posts_collected, posts_new, posts_duplicate,
                posts_transcribed, status, error_message, log_id,
            ),
        )
        conn.commit()

    # ═══════════════════════════════════════════
    # Scrape Targets
    # ═══════════════════════════════════════════

    @staticmethod
    def save_targets(conn: sqlite3.Connection, targets: list[ScrapeTarget]):
        """保存目标列表到本地缓存"""
        conn.executemany(
            """INSERT OR REPLACE INTO scrape_targets
               (douyin_id, name, target_type, status, notes)
               VALUES (?, ?, ?, ?, ?)""",
            [
                (t.douyin_id, t.name, t.target_type.value, t.status.value, t.notes)
                for t in targets
            ],
        )
        conn.commit()

    @staticmethod
    def get_active_targets(conn: sqlite3.Connection) -> list[ScrapeTarget]:
        """获取活跃的采集目标"""
        cursor = conn.execute(
            "SELECT * FROM scrape_targets WHERE status = 'active'"
        )
        return [
            ScrapeTarget(
                name=row["name"],
                target_type=TargetType(row["target_type"]),
                douyin_id=row["douyin_id"],
                status=TargetStatus(row["status"]),
                notes=row["notes"],
            )
            for row in cursor.fetchall()
        ]

    # ═══════════════════════════════════════════
    # 内部方法
    # ═══════════════════════════════════════════

    @staticmethod
    def _row_to_post(row: sqlite3.Row) -> Post:
        """将数据库行转为 Post 模型"""
        d = dict(row)
        return Post(
            post_id=d["post_id"],
            author_name=d["author_name"],
            author_id=d["author_id"],
            video_title=d["video_title"],
            video_desc=d["video_desc"],
            video_url=d["video_url"],
            hashtags=json.loads(d["hashtags"]) if d.get("hashtags") else [],
            # 转写
            transcribed_text=d.get("transcribed_text", ""),
            transcribed_text_raw=d.get("transcribed_text_raw", ""),
            ai_refined_text=d.get("ai_refined_text", ""),
            # 任务状态
            task_status=TaskStatus(d.get("task_status", "new")),
            retry_count=d.get("retry_count", 0),
            error_msg=d.get("error_msg", ""),
            # 去重
            content_hash=d.get("content_hash", ""),
            # Content Engine
            content_type=d.get("content_type", ""),
            content_type_confidence=d.get("content_type_confidence", 0.0),
            quality_score=d.get("quality_score", 0.0),
            quality_dimensions=d.get("quality_dimensions", "{}"),
            template_used=d.get("template_used", ""),
            regenerated=bool(d.get("regenerated", 0)),
            # 时间
            publish_time=(
                datetime.fromisoformat(d["publish_time"])
                if d.get("publish_time") else None
            ),
            collected_at=datetime.fromisoformat(d["collected_at"]),
            # 来源
            source_target=d["source_target"],
            source_type=TargetType(d["source_type"]),
        )
