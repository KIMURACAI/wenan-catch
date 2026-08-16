-- 抖音文案采集系统 - 数据库表结构
-- V2: 新增任务状态机、content_hash、重试机制

-- 已采集的视频数据
CREATE TABLE IF NOT EXISTS posts (
    post_id             TEXT PRIMARY KEY,         -- 抖音 aweme_id
    author_name         TEXT NOT NULL DEFAULT '',
    author_id           TEXT NOT NULL DEFAULT '',
    video_title         TEXT DEFAULT '',
    video_desc          TEXT DEFAULT '',           -- 页面文案
    video_url           TEXT DEFAULT '',
    hashtags            TEXT DEFAULT '[]',         -- JSON array

    -- ASR 转写
    transcribed_text    TEXT DEFAULT '',           -- 精炼后的转写文案
    transcribed_text_raw TEXT DEFAULT '',          -- 原始转写结果

    -- AI 润色
    ai_refined_text     TEXT DEFAULT '',           -- AI 润色后的文案

    -- 任务状态机
    task_status         TEXT DEFAULT 'new',        -- new|downloading|downloaded|asr_pending|asr_ok|ai_pending|ai_ok|done|failed
    retry_count         INTEGER DEFAULT 0,         -- 重试次数
    error_msg           TEXT DEFAULT '',           -- 最后的错误信息

    -- 去重
    content_hash        TEXT DEFAULT '',           -- 转写文本 hash

    -- Content Engine
    content_type               TEXT DEFAULT '',     -- 分类结果
    content_type_confidence    REAL DEFAULT 0.0,    -- 分类置信度
    quality_score              REAL DEFAULT 0.0,    -- 质量总分
    quality_dimensions         TEXT DEFAULT '{}',   -- 各维度得分 JSON
    template_used              TEXT DEFAULT '',     -- 使用的模板
    regenerated                INTEGER DEFAULT 0,   -- 是否重写过

    -- 时间
    publish_time        TEXT,                      -- ISO 8601
    collected_at        TEXT NOT NULL,

    -- 来源
    source_target       TEXT DEFAULT '',           -- 来源目标名称
    source_type         TEXT DEFAULT 'user'        -- user | hashtag
);

-- 运行日志
CREATE TABLE IF NOT EXISTS run_logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date            TEXT NOT NULL,             -- "2026-07-09"
    started_at          TEXT NOT NULL,
    finished_at         TEXT,
    targets_count       INTEGER DEFAULT 0,
    posts_collected     INTEGER DEFAULT 0,
    posts_new           INTEGER DEFAULT 0,
    posts_duplicate     INTEGER DEFAULT 0,
    posts_transcribed   INTEGER DEFAULT 0,
    status              TEXT DEFAULT 'running',     -- running | success | failed
    error_message       TEXT DEFAULT ''
);

-- 采集目标缓存
CREATE TABLE IF NOT EXISTS scrape_targets (
    douyin_id           TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    target_type         TEXT NOT NULL,             -- user | hashtag
    status              TEXT DEFAULT 'active',      -- active | paused
    notes               TEXT DEFAULT ''
);

-- 索引
-- idx_posts_task_status 在迁移代码中创建（兼容旧表）
CREATE INDEX IF NOT EXISTS idx_posts_collected_at ON posts(collected_at);
CREATE INDEX IF NOT EXISTS idx_posts_publish_time ON posts(publish_time);
CREATE INDEX IF NOT EXISTS idx_posts_source ON posts(source_target, source_type);
CREATE INDEX IF NOT EXISTS idx_run_logs_date ON run_logs(run_date DESC);
