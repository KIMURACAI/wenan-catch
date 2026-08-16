"""
数据库连接管理

提供可重入的上下文管理器，支持嵌套使用，自动建表和连接管理。
"""
import sqlite3
from pathlib import Path
from typing import Optional

from loguru import logger


class DatabaseManager:
    """SQLite 数据库连接管理器（可重入）"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._depth = 0  # 嵌套深度，防止内层退出时关闭连接

    def __enter__(self):
        """同步上下文入口（可重入）"""
        if self._depth == 0:
            self.connect()
        self._depth += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._depth -= 1
        if self._depth == 0:
            self.close()

    def connect(self):
        """建立数据库连接并初始化表结构"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")

        self._init_schema()
        logger.debug(f"数据库已连接: {self.db_path}")

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("数据库连接已关闭")

    def _init_schema(self):
        """初始化表结构并执行迁移"""
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            statements = []
            for line in schema_sql.split("\n"):
                stripped = line.strip()
                if stripped.startswith("--"):
                    continue
                statements.append(line)
            clean_sql = "\n".join(statements)
            self.conn.executescript(clean_sql)
            self.conn.commit()
            logger.debug("数据库表结构已初始化")

        # V2 迁移：新增列
        self._migrate_v2()
        # V3 迁移：Content Engine 列
        self._migrate_v3()

    def _migrate_v3(self):
        """V3 数据库迁移：新增 content_type、quality_score 等列"""
        existing_cols = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(posts)").fetchall()
        }
        ce_cols = [
            ("content_type", "TEXT DEFAULT ''"),
            ("content_type_confidence", "REAL DEFAULT 0.0"),
            ("quality_score", "REAL DEFAULT 0.0"),
            ("quality_dimensions", "TEXT DEFAULT '{}'"),
            ("template_used", "TEXT DEFAULT ''"),
            ("regenerated", "INTEGER DEFAULT 0"),
        ]
        for col_name, col_type in ce_cols:
            if col_name not in existing_cols:
                try:
                    self.conn.execute(f"ALTER TABLE posts ADD COLUMN {col_name} {col_type}")
                    logger.debug(f"数据库迁移: 添加列 {col_name}")
                except Exception as e:
                    logger.warning(f"数据库迁移 {col_name} 失败: {e}")
        self.conn.commit()

    def _migrate_v2(self):
        """V2 数据库迁移：新增 task_status、content_hash 等列"""
        existing_cols = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(posts)").fetchall()
        }

        migrations = [
            ("transcribed_text_raw", "TEXT DEFAULT ''"),
            ("ai_refined_text", "TEXT DEFAULT ''"),
            ("task_status", "TEXT DEFAULT 'new'"),
            ("retry_count", "INTEGER DEFAULT 0"),
            ("error_msg", "TEXT DEFAULT ''"),
            ("content_hash", "TEXT DEFAULT ''"),
        ]

        for col_name, col_type in migrations:
            if col_name not in existing_cols:
                try:
                    self.conn.execute(
                        f"ALTER TABLE posts ADD COLUMN {col_name} {col_type}"
                    )
                    logger.debug(f"数据库迁移: 添加列 {col_name}")
                except Exception as e:
                    logger.warning(f"数据库迁移 {col_name} 失败: {e}")

        # 迁移后创建新索引
        try:
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_task_status ON posts(task_status)")
        except Exception:
            pass

        # 重新读取列（ALIER TABLE 之后）
        cols_after = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(posts)").fetchall()
        }

        # 迁移旧数据：transcribe_status -> task_status
        if "transcribe_status" in cols_after and "task_status" in cols_after:
            self.conn.execute("""
                UPDATE posts SET task_status = 'done'
                WHERE transcribe_status = 'completed' AND task_status = 'new'
            """)
            self.conn.execute("""
                UPDATE posts SET task_status = 'failed'
                WHERE transcribe_status = 'failed' AND task_status = 'new'
            """)
            self.conn.execute("""
                UPDATE posts SET task_status = 'done'
                WHERE transcribe_status = 'none' AND task_status = 'new'
            """)

        self.conn.commit()

    @property
    def is_connected(self) -> bool:
        return self.conn is not None
