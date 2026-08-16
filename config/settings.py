"""
配置管理模块 - 两级配置体系

优先级: .env (密钥/Token) > config.yaml (非敏感参数) > 默认值

使用 Pydantic Settings 实现类型安全和自动加载。
"""
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class Settings(BaseSettings):
    """全局配置，合并 .env 和 config.yaml"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 飞书凭证 ──
    feishu_app_id: str = Field(default="", alias="FEISHU_APP_ID")
    feishu_app_secret: str = Field(default="", alias="FEISHU_APP_SECRET")
    feishu_bitable_app_token: str = Field(default="", alias="FEISHU_BITABLE_APP_TOKEN")
    feishu_target_table_id: str = Field(default="", alias="FEISHU_TARGET_TABLE_ID")
    feishu_document_folder_token: str = Field(default="", alias="FEISHU_DOCUMENT_FOLDER_TOKEN")

    # ── 运行时 ──
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    daily_run_time: str = Field(default="08:00", alias="DAILY_RUN_TIME")

    # ── 项目路径 (基于项目根目录) ──
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = Field(default="data")
    log_dir: Path = Field(default="logs")

    # ── 抖音采集 ──
    douyin_base_url: str = "https://www.douyin.com"
    douyin_user_url_template: str = "https://www.douyin.com/user/{sec_uid}"
    douyin_hashtag_url_template: str = "https://www.douyin.com/hashtag/{hashtag_id}"
    douyin_scroll_pause: float = 2.0
    douyin_min_scroll_px: int = 300
    douyin_max_scroll_px: int = 700
    douyin_min_delay: float = 0.3
    douyin_max_delay: float = 0.8
    douyin_max_scroll: int = 15
    douyin_page_timeout: int = 30
    douyin_max_videos: int = 20
    douyin_min_videos: int = 3
    douyin_cookie_path: str = "data/cookies/douyin_cookies.json"

    # ── 反检测 ──
    stealth_viewport_width: int = 1920
    stealth_viewport_height: int = 1080
    stealth_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
    stealth_locale: str = "zh-CN"
    stealth_timezone: str = "Asia/Shanghai"

    # ── 数据库 ──
    storage_database_path: str = "data/wenan_catch.db"
    storage_dedup_days: int = 30

    # ── 语音识别 ──
    transcriber_engine: str = "whisper"
    transcriber_model: str = "tiny"
    transcriber_language: str = "zh"
    transcriber_temp_dir: str = "data/temp_videos"
    transcriber_cleanup: bool = True

    # 火山引擎 ASR
    volc_access_key: str = Field(default="", alias="VOLC_ACCESS_KEY")
    volc_secret_key: str = Field(default="", alias="VOLC_SECRET_KEY")
    volc_app_id: str = Field(default="", alias="VOLC_APP_ID")
    volc_app_key: str = Field(default="", alias="VOLC_APP_KEY")

    # DeepSeek AI
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")

    # Content Engine
    ce_enabled: bool = True
    ce_quality_threshold: float = 85.0
    ce_max_regenerate_attempts: int = 2
    ce_sample_save_threshold: float = 85.0

    # ── 飞书 ──
    feishu_api_base: str = "https://open.feishu.cn/open-apis"
    feishu_daily_doc_template: str = "抖音文案日报 - {date}"
    feishu_rate_limit: int = 5

    # ── YAML 配置缓存 ──
    _yaml_config: dict = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_yaml()
        self._resolve_paths()

    def _load_yaml(self):
        """加载 config.yaml 的非敏感配置，覆盖默认值"""
        yaml_path = self.project_root / "config" / "config.yaml"
        if not yaml_path.exists():
            return

        with open(yaml_path, "r", encoding="utf-8") as f:
            self._yaml_config = yaml.safe_load(f) or {}

        # 将 YAML 值映射到 Pydantic 字段
        mapping = {
            # 项目
            ("project", "data_dir"): "data_dir",
            ("project", "log_dir"): "log_dir",
            # 抖音
            ("douyin", "base_url"): "douyin_base_url",
            ("douyin", "user_url_template"): "douyin_user_url_template",
            ("douyin", "hashtag_url_template"): "douyin_hashtag_url_template",
            ("douyin", "scroll_pause_seconds"): "douyin_scroll_pause",
            ("douyin", "max_scroll_attempts"): "douyin_max_scroll",
            ("douyin", "page_load_timeout_seconds"): "douyin_page_timeout",
            ("douyin", "max_videos_per_target"): "douyin_max_videos",
            ("douyin", "min_videos_per_target"): "douyin_min_videos",
            ("douyin", "cookie_path"): "douyin_cookie_path",
            # 反检测
            ("stealth", "viewport_width"): "stealth_viewport_width",
            ("stealth", "viewport_height"): "stealth_viewport_height",
            ("stealth", "user_agent"): "stealth_user_agent",
            ("stealth", "locale"): "stealth_locale",
            ("stealth", "timezone"): "stealth_timezone",
            # 存储
            ("storage", "database_path"): "storage_database_path",
            ("storage", "dedup_window_days"): "storage_dedup_days",
            # 语音识别
            ("transcriber", "engine"): "transcriber_engine",
            ("transcriber", "model_size"): "transcriber_model",
            ("transcriber", "language"): "transcriber_language",
            ("transcriber", "temp_dir"): "transcriber_temp_dir",
            ("transcriber", "cleanup_temp_files"): "transcriber_cleanup",
            # Content Engine
            ("content_engine", "enabled"): "ce_enabled",
            ("content_engine", "quality_threshold"): "ce_quality_threshold",
            ("content_engine", "max_regenerate_attempts"): "ce_max_regenerate_attempts",
            ("content_engine", "sample_save_threshold"): "ce_sample_save_threshold",
            # 飞书
            ("feishu", "daily_doc_title_template"): "feishu_daily_doc_template",
            ("feishu", "rate_limit"): "feishu_rate_limit",
        }

        for (section, key), attr in mapping.items():
            section_data = self._yaml_config.get(section, {})
            if key in section_data and section_data[key] is not None:
                try:
                    setattr(self, attr, section_data[key])
                except Exception:
                    pass  # 忽略类型转换错误

    def _resolve_paths(self):
        """将相对路径转为绝对路径"""
        for attr in ["data_dir", "log_dir", "douyin_cookie_path",
                      "storage_database_path", "transcriber_temp_dir"]:
            raw = getattr(self, attr)
            if raw and not Path(raw).is_absolute():
                setattr(self, attr, str(self.project_root / raw))

    @property
    def resolved_data_dir(self) -> Path:
        return Path(self.data_dir)

    @property
    def resolved_log_dir(self) -> Path:
        return Path(self.log_dir)

    @property
    def resolved_db_path(self) -> Path:
        return Path(self.storage_database_path)
