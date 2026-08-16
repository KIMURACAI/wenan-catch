"""
流程编排器 - 协调整个采集流程

职责:
  1. 获取目标列表
  2. 采集 -> 去重 -> 保存
  3. 下载 -> ASR -> AI润色 -> 飞书
  4. 记录日志

不做:
  - 不处理业务细节（各模块自行负责）
  - 不直接读写数据库（通过 Repository）
  - 不管理浏览器生命周期细节
"""
import asyncio
import random
import traceback
from datetime import datetime, timezone, timedelta
from typing import Optional

from loguru import logger

from config import settings
from models.schemas import (
    Post, ScrapeTarget, RunLog, TargetType, TargetStatus, TaskStatus,
)
from storage.database import DatabaseManager
from storage.repository import Repository
from browser.manager import BrowserManager
from extractors.user_extractor import UserExtractor
from extractors.hashtag_extractor import HashtagExtractor
from pipeline.dedup import DedupEngine
from utils.exceptions import DownloadError, ASRError


class Orchestrator:
    """流程编排器"""

    def __init__(
        self,
        headless: bool = True,
        enable_transcribe: bool = True,
        enable_ai_refine: bool = False,
        dry_run: bool = False,
    ):
        """
        Args:
            headless: 无头浏览器
            enable_transcribe: 启用语音转文字
            enable_ai_refine: 启用 AI 润色
            dry_run: 试运行（不写入飞书）
        """
        self.headless = headless
        self.enable_transcribe = enable_transcribe
        self.enable_ai_refine = enable_ai_refine
        self.dry_run = dry_run

        self.run_log = RunLog(
            run_date=datetime.now().strftime("%Y-%m-%d"),
            started_at=datetime.now(),
        )
        self.all_new_posts: list[Post] = []
        self.failed_targets: list[str] = []
        self.report_doc_url: Optional[str] = None

    async def run(self):
        """执行一次完整采集流程"""
        logger.info("=" * 50)
        logger.info("抖音文案采集系统 V2")
        logger.info(f"日期: {self.run_log.run_date}")
        logger.info(f"试运行: {self.dry_run}")
        logger.info(f"语音转写: {self.enable_transcribe}")
        logger.info(f"AI润色: {self.enable_ai_refine}")
        logger.info("=" * 50)

        try:
            with DatabaseManager(settings.storage_database_path) as db:
                repo = Repository()
                dedup = DedupEngine(db.conn)

                # 1. 获取目标
                targets = await self._get_targets(db, repo)
                if not targets:
                    logger.warning("没有活跃的采集目标")
                    return
                self.run_log.targets_count = len(targets)
                logger.info(f"共 {len(targets)} 个目标")

                # 2. 采集新视频
                async with BrowserManager(headless=self.headless) as browser:
                    context = await browser.create_context(load_cookies=True)
                    if not await browser.check_login_status(context):
                        logger.error("登录失效，请运行 --mode login")
                        self.run_log.status = "failed"
                        self.run_log.error_message = "登录状态失效"
                        return

                    for i, target in enumerate(targets):
                        logger.info(
                            f"\n--- 进度 {i+1}/{len(targets)}: "
                            f"{target.name} ({target.target_type.value}) ---"
                        )
                        await self._scrape_target(browser, context, target, dedup, db)
                        if i < len(targets) - 1:
                            delay = random.uniform(5, 8)
                            logger.info(f"等待 {delay:.1f}s...")
                            await asyncio.sleep(delay)

                # 3. 按账号逐个处理后置流程（下载 -> ASR -> AI）
                for target in targets:
                    # 只处理该账号有待处理的视频
                    account_posts = [p for p in self.all_new_posts if p.source_target == target.name]
                    if not account_posts:
                        logger.info(f"【{target.name}】无新增视频，跳过")
                        continue

                    logger.info(f"{'='*50}")
                    logger.info(f"【{target.name}】开始处理 ({len(account_posts)} 条)")
                    logger.info(f"{'='*50}")

                    try:
                        if self.enable_transcribe:
                            await self._run_asr_pipeline(db, repo, account_posts)
                            # 从数据库重新读取，获取最新状态
                            fresh_posts = []
                            for p in account_posts:
                                fresh = repo.get_post(db.conn, p.post_id)
                                if fresh:
                                    fresh_posts.append(fresh)
                            account_posts = fresh_posts

                        if self.enable_ai_refine:
                            await self._run_ai_pipeline(db, repo, account_posts)
                    except Exception as e:
                        logger.error(f"【{target.name}】处理失败: {e}")
                        continue

                    logger.info(f"【{target.name}】处理完成")
                    logger.info(f"{'='*50}")

                # 4. 清理缓存
                await self._cleanup_cache()

                # 5. 导出
                if not self.dry_run and self.all_new_posts:
                    await self._generate_report(db, repo)

                self.run_log.status = "success"
                self._print_summary()

        except Exception as e:
            logger.error(f"流程异常终止: {e}")
            logger.error(traceback.format_exc())
            self.run_log.status = "failed"
            self.run_log.error_message = str(e)
        finally:
            self.run_log.finished_at = datetime.now()
            self._save_run_log()

    # ═══════════════════════════════════════════
    # 目标管理
    # ═══════════════════════════════════════════

    async def _get_targets(self, db, repo) -> list[ScrapeTarget]:
        """获取采集目标（飞书 -> 本地缓存）"""
        targets = await self._from_feishu(db, repo)
        if not targets:
            logger.info("使用本地缓存目标")
            with db:
                targets = repo.get_active_targets(db.conn)
        return targets

    async def _from_feishu(self, db, repo) -> list[ScrapeTarget]:
        """从飞书多维表格获取目标"""
        if not settings.feishu_app_id or not settings.feishu_app_secret:
            return []
        try:
            from feishu.bitable import BitableClient
            auth = self._feishu_auth()
            if not auth:
                return []
            bitable = BitableClient(
                auth,
                settings.feishu_bitable_app_token,
                settings.feishu_target_table_id,
            )
            targets = await bitable.get_targets()
            if targets:
                with db:
                    repo.save_targets(db.conn, targets)
            return targets
        except Exception as e:
            logger.warning(f"飞书获取目标失败: {e}")
            return []

    def _feishu_auth(self):
        from feishu.auth import FeishuAuth
        try:
            return FeishuAuth(settings.feishu_app_id, settings.feishu_app_secret)
        except Exception as e:
            logger.warning(f"飞书认证失败: {e}")
            return None

    # ═══════════════════════════════════════════
    # 采集
    # ═══════════════════════════════════════════

    async def _scrape_target(self, browser, context, target, dedup, db):
        """采集单个目标 -> 去重 -> 保存"""
        logger.info(f"{'='*50}")
        logger.info(f"【{target.name}】开始采集")
        logger.info(f"{'='*50}")

        try:
            if target.target_type == TargetType.USER:
                extractor = UserExtractor(context)
            else:
                extractor = HashtagExtractor(context)

            posts = await extractor.extract(
                target, max_videos=settings.douyin_max_videos
            )
            if not posts:
                logger.info(f"【{target.name}】无视频")
                return

            collected = len(posts)
            new_posts, duplicates = dedup.filter_new_posts(posts)
            dup_count = len(duplicates)
            logger.info(f"【{target.name}】采集 {collected} 条，去重后新 {len(new_posts)} 条，重复 {dup_count} 条")

            if new_posts:
                new_posts = dedup.filter_new_by_hash(new_posts)
                hash_dup = len(new_posts)  # 先记录hash过滤前
                logger.info(f"【{target.name}】content_hash 去重后 {len(new_posts)} 条")

            # 每天每个目标最多新增3篇
            MAX_NEW_PER_TARGET = 3
            if len(new_posts) > MAX_NEW_PER_TARGET:
                logger.info(f"【{target.name}】采集到 {len(new_posts)} 条新视频，限制为前 {MAX_NEW_PER_TARGET} 条")
                new_posts = new_posts[:MAX_NEW_PER_TARGET]

            if new_posts:
                repo = Repository()
                repo.save_posts(db.conn, new_posts)
                self.all_new_posts.extend(new_posts)
                logger.info(f"✅ 【{target.name}】{len(new_posts)} 条新视频已保存")
            else:
                logger.info(f"【{target.name}】无新视频")

            self.run_log.posts_collected += collected
            self.run_log.posts_new += len(new_posts)
            self.run_log.posts_duplicate += dup_count

        except Exception as e:
            logger.error(f"【{target.name}】采集失败: {e}")
            logger.error(traceback.format_exc())
            self.failed_targets.append(target.name)

    # ═══════════════════════════════════════════
    # ASR Pipeline: 下载 -> 转写
    # ═══════════════════════════════════════════

    async def _run_asr_pipeline(self, db, repo, posts):
        """下载 -> ASR 转写，支持断点续传"""
        logger.info("\n=== ASR Pipeline ===")

        # 找出需要下载或转写的
        pending = [
            p for p in posts
            if p.task_status in (TaskStatus.NEW, TaskStatus.DOWNLOADED)
        ]
        if not pending:
            logger.info("所有视频已完成或无需 ASR")
            return

        logger.info(f"{len(pending)} 条待处理")

        from transcriber.downloader import VideoDownloader
        from transcriber.audio import AudioExtractor
        from transcriber.volc_asr import transcribe_audio as volc_transcribe
        from transcriber.refiner import refine_transcription

        downloader = VideoDownloader()
        audio_extractor = AudioExtractor()

        for i, post in enumerate(pending):
            logger.info(f"\n--- ASR {i+1}/{len(pending)}: {post.post_id} ---")

            # Step 1: 检查音频缓存
            cached_audio = downloader.get_cached_audio(post.post_id)
            if cached_audio:
                audio_path = cached_audio
                logger.debug("音频缓存命中")
            else:
                # Step 2: 下载视频
                try:
                    repo.update_post_status(
                        db.conn, post.post_id, TaskStatus.DOWNLOADING
                    )
                    urls = post.video_urls or [post.video_url] if post.video_url else []
                    if not urls:
                        logger.warning(f"无播放地址")
                        repo.update_post_status(
                            db.conn, post.post_id, TaskStatus.FAILED, "无播放地址"
                        )
                        continue

                    video_path = await downloader.download(urls, post.post_id)

                    # Step 3: 提取音频
                    audio_path = audio_extractor.extract_audio(video_path)
                    if not audio_path:
                        raise DownloadError("音频提取失败")

                    # 缓存音频
                    downloader.cache_audio(post.post_id, audio_path)

                    repo.update_post_status(
                        db.conn, post.post_id, TaskStatus.DOWNLOADED
                    )

                except (DownloadError, Exception) as e:
                    logger.error(f"下载失败: {e}")
                    repo.increment_retry(
                        db.conn, post.post_id, str(e)[:200]
                    )
                    continue

            # Step 4: ASR 转写
            try:
                repo.update_post_status(
                    db.conn, post.post_id, TaskStatus.ASR_PENDING
                )
                result = await volc_transcribe(audio_path)
                text = result.get("text", "")

                if text:
                    # 先精炼
                    refined = refine_transcription(text)
                    final_text = refined.text
                    raw_text = text  # 保存原始

                    # 检测无语音内容（ASR结果过短，基本是噪声音乐）
                    import re
                    clean_text = re.sub(r'#\S+|@\S+|https?://\S+', '', final_text).strip()
                    clean_text = re.sub(r'[^一-鿿]', '', clean_text)
                    if len(clean_text) < 5:
                        logger.warning(f"无有效语音内容（仅{len(clean_text)}个中文字），跳过")
                        repo.update_post_status(
                            db.conn, post.post_id, TaskStatus.FAILED, "无有效语音内容"
                        )
                        continue

                    if refined.is_watermark:
                        logger.warning("水印噪音，跳过")
                        repo.update_post_status(
                            db.conn, post.post_id, TaskStatus.FAILED, "水印噪音"
                        )
                    elif final_text:
                        repo.update_transcription(
                            db.conn, post.post_id,
                            transcribed_text=final_text,
                            transcribed_text_raw=raw_text,
                            task_status=TaskStatus.ASR_OK,
                        )
                        self.run_log.posts_transcribed += 1
                        logger.info(f"✅ ASR OK ({len(final_text)} 字)")
                    else:
                        repo.update_post_status(
                            db.conn, post.post_id, TaskStatus.FAILED, "精炼后为空"
                        )
                else:
                    err = result.get("error", "未知错误")
                    repo.update_post_status(
                        db.conn, post.post_id, TaskStatus.FAILED, err
                    )

            except Exception as e:
                logger.error(f"ASR 失败: {e}")
                repo.increment_retry(db.conn, post.post_id, str(e)[:200])

            await downloader.cleanup(post.post_id)

            if i < len(pending) - 1:
                await asyncio.sleep(0.5)

    # ═══════════════════════════════════════════
    # AI Pipeline: 润色
    # ═══════════════════════════════════════════

    async def _run_ai_pipeline(self, db, repo, posts):
        """Content Engine: 分类 -> 分析 -> 模板匹配 -> 改写 -> 质检"""
        logger.info("\n=== Content Engine ===")

        pending = [
            p for p in posts
            if p.task_status == TaskStatus.ASR_OK
        ]
        if not pending:
            logger.info("没有需要处理的内容")
            return

        logger.info(f"{len(pending)} 条待处理")

        from ai.provider import AIProvider
        from content_engine.pipeline import ContentEnginePipeline

        provider = AIProvider()
        ce = ContentEnginePipeline(provider)

        for i, post in enumerate(pending):
            logger.info(f"\n--- CE {i+1}/{len(pending)}: {post.post_id} ---")
            if not post.transcribed_text:
                continue

            try:
                repo.update_post_status(
                    db.conn, post.post_id, TaskStatus.AI_PENDING
                )

                # Content Engine 完整流程
                result = await ce.process(
                    post.transcribed_text,
                    source=post.source_target,
                )

                if result.refined_text and result.refined_text != post.transcribed_text:
                    repo.update_ai_refined(
                        db.conn, post.post_id,
                        ai_refined_text=result.refined_text,
                        task_status=TaskStatus.AI_OK,
                    )
                    self.run_log.posts_transcribed += 1
                    logger.info(
                        f"✅ 整理完成 ({len(result.refined_text)}字)"
                    )
                else:
                    # 改写无变化，存原文
                    repo.update_ai_refined(
                        db.conn, post.post_id,
                        ai_refined_text=post.transcribed_text,
                        task_status=TaskStatus.AI_OK,
                    )
                    logger.info("CE 无变化，使用原文")

            except Exception as e:
                logger.error(f"CE 处理失败: {e}")
                repo.update_ai_refined(
                    db.conn, post.post_id,
                    ai_refined_text=post.transcribed_text,
                    task_status=TaskStatus.AI_OK,
                )

            if i < len(pending) - 1:
                await asyncio.sleep(0.5)

    # ═══════════════════════════════════════════
    # 缓存清理
    # ═══════════════════════════════════════════

    async def _cleanup_cache(self):
        """完成后清理所有缓存文件"""
        from transcriber.downloader import VideoDownloader
        try:
            d = VideoDownloader()
            await d.cleanup_all()
            # 也清空 cache/videos/ 和 cache/audios/
            import shutil
            for cache_dir in [d.cache_dir, d.audio_cache_dir]:
                if cache_dir.exists():
                    for f in cache_dir.glob("*"):
                        if f.is_file():
                            f.unlink()
            logger.info("缓存已清理")
        except Exception as e:
            logger.debug(f"缓存清理失败: {e}")

    # ═══════════════════════════════════════════
    # 飞书报告
    # ═══════════════════════════════════════════

    async def _generate_report(self, db, repo):
        """将新文案追加到对应账号的飞书文档"""
        logger.info("\n=== 飞书文档追加 ===")

        if not self.all_new_posts:
            logger.info("今日无新内容")
            return

        if not settings.feishu_app_id or not settings.feishu_app_secret:
            logger.warning("飞书未配置")
            return

        try:
            from feishu.auth import FeishuAuth
            from feishu.document import DocumentClient
            from feishu.formatter import DocumentBuilder

            auth = FeishuAuth(settings.feishu_app_id, settings.feishu_app_secret)
            token = await auth.get_token()
            if not token:
                return

            doc_client = DocumentClient(
                auth,
                folder_token=settings.feishu_document_folder_token or None,
            )

            builder = DocumentBuilder()

            # 按目标分组
            posts_by_target: dict[str, list[Post]] = {}
            for post in self.all_new_posts:
                posts_by_target.setdefault(post.source_target, []).append(post)

            # 每个目标写入对应文档
            for target_name, posts in posts_by_target.items():
                logger.info(f"写入 {target_name} 的文档 ({len(posts)} 条)")

                doc_token, doc_url = await doc_client.ensure_account_document(target_name)
                if not doc_token:
                    logger.warning(f"无法创建/获取 {target_name} 的文档")
                    continue

                blocks = builder.build_entry_blocks(posts, target_name)
                if await doc_client.append_content(doc_token, blocks):
                    logger.info(f"✅ {target_name}: {len(posts)} 条已追加")
                self.report_doc_url = doc_url

        except ImportError:
            logger.warning("飞书 SDK 未安装")
        except Exception as e:
            logger.error(f"飞书追加失败: {e}")
            logger.error(traceback.format_exc())

    # ═══════════════════════════════════════════
    # 日志 / 总结
    # ═══════════════════════════════════════════

    def _print_summary(self):
        """打印运行总结"""
        logger.info("\n" + "=" * 50)
        logger.info("📊 运行总结")
        logger.info("=" * 50)
        logger.info(f"收集总数:     {self.run_log.posts_collected}")
        logger.info(f"新增视频:     {self.run_log.posts_new}")
        logger.info(f"重复视频:     {self.run_log.posts_duplicate}")
        logger.info(f"语音转写:     {self.run_log.posts_transcribed}")
        logger.info(f"失败目标:     {', '.join(self.failed_targets) if self.failed_targets else '无'}")
        logger.info(f"运行状态:     {self.run_log.status}")
        if self.report_doc_url:
            logger.info(f"日报地址:     {self.report_doc_url}")
        logger.info("=" * 50)

    def _save_run_log(self):
        """保存运行日志"""
        try:
            with DatabaseManager(settings.storage_database_path) as db:
                log_id = Repository.create_run_log(db.conn, self.run_log)
                if self.run_log.finished_at:
                    Repository.complete_run_log(
                        db.conn,
                        log_id=log_id,
                        posts_collected=self.run_log.posts_collected,
                        posts_new=self.run_log.posts_new,
                        posts_duplicate=self.run_log.posts_duplicate,
                        posts_transcribed=self.run_log.posts_transcribed,
                        status=self.run_log.status,
                        error_message=self.run_log.error_message,
                    )
        except Exception as e:
            logger.error(f"保存运行日志失败: {e}")
