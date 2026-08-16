"""
指定用户批量扒取 - 扒取指定用户最新N条视频，完整走ASR+AI

用法:
  python backfill.py 奇门小道            # 默认10条
  python backfill.py 木清 15             # 指定15条
  python backfill.py "小千师兄" 15       # 带空格的名称要加引号

异常处理:
  - 视频不足N条 → 实际采集到多少处理多少，不报错
  - 部分视频下载失败 → 成功多少处理多少
  - 全部失败 → 输出明确错误信息
"""
import sys
import asyncio
import subprocess
import time

sys.path.insert(0, ".")

from loguru import logger
from config import settings
from models.schemas import Post, ScrapeTarget, TargetType, TargetStatus, TaskStatus
from storage.database import DatabaseManager
from storage.repository import Repository
from pipeline.dedup import DedupEngine
from browser.manager import BrowserManager
from extractors.user_extractor import UserExtractor
from extractors.hashtag_extractor import HashtagExtractor


async def main():
    start_time = time.time()

    # ── 参数解析 ──
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target_name = sys.argv[1]
    try:
        max_count = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
        if max_count < 1:
            print("数量必须 >= 1")
            sys.exit(1)
    except ValueError:
        print("数量参数必须是数字")
        sys.exit(1)

    logger.info(f"指定用户: {target_name} ({max_count}条)")

    # ── 1. 获取目标信息 ──
    target = None
    with DatabaseManager(settings.storage_database_path) as db:
        targets = Repository.get_active_targets(db.conn)
        for t in targets:
            if t.name == target_name:
                target = t
                break

    if not target:
        logger.info(f"本地未找到 {target_name}，尝试从飞书获取...")
        try:
            from feishu.auth import FeishuAuth
            from feishu.bitable import BitableClient
            auth = FeishuAuth(settings.feishu_app_id, settings.feishu_app_secret)
            bitable = BitableClient(
                auth, settings.feishu_bitable_app_token, settings.feishu_target_table_id,
            )
            for t in await bitable.get_targets():
                if t.name == target_name:
                    target = t
                    break
        except Exception as e:
            logger.error(f"从飞书获取失败: {e}")

    if not target:
        logger.error(f"未找到目标: {target_name}")
        print("\n可用目标:")
        with DatabaseManager(settings.storage_database_path) as db:
            for t in Repository.get_active_targets(db.conn):
                print(f"  - {t.name}")
        sys.exit(1)

    logger.info(f"目标: {target.name}")

    # ── 2. 采集视频 ──
    posts = []
    try:
        async with BrowserManager(headless=True) as browser:
            context = await browser.create_context(load_cookies=True)
            if not await browser.check_login_status(context):
                logger.error("登录状态失效，请运行 --mode login 重新登录")
                sys.exit(1)

            extractor = (UserExtractor if target.target_type == TargetType.USER else HashtagExtractor)(context)
            posts = await extractor.extract(target, max_videos=max_count)

        if not posts:
            logger.error("未获取到视频（可能该账号未发布视频或页面加载失败）")
            sys.exit(1)

        actual = len(posts)
        if actual < max_count:
            logger.info(f"该账号仅有 {actual} 条视频（不足 {max_count} 条），全部采集")
        else:
            logger.info(f"采集到 {actual} 条视频")

    except Exception as e:
        logger.error(f"采集失败: {e}")
        sys.exit(1)

    # ── 3. 去重保存 ──
    with DatabaseManager(settings.storage_database_path) as db:
        dedup = DedupEngine(db.conn)
        new_posts, dup = dedup.filter_new_posts(posts)
        logger.info(f"新视频: {len(new_posts)} 条, 已存在: {len(dup)} 条")

        if not new_posts:
            logger.info("所有视频已在数据库中，无需处理")
            print("\n✅ 所有视频已在数据库中，无需重复处理")
            return

        repo = Repository()
        repo.save_posts(db.conn, new_posts)
        logger.info(f"已保存 {len(new_posts)} 条")

    # ── 4. ASR + AI 处理 ──
    from pipeline.orchestrator import Orchestrator
    orch = Orchestrator(headless=True, enable_transcribe=True, enable_ai_refine=True, dry_run=False)
    success_count = 0

    with DatabaseManager(settings.storage_database_path) as db:
        repo = Repository()

        logger.info(f"\n开始ASR转写 ({len(new_posts)} 条，预计耗时较长)...")
        asr_start = time.time()
        await orch._run_asr_pipeline(db, repo, new_posts)
        asr_elapsed = time.time() - asr_start
        logger.info(f"ASR阶段完成，耗时 {asr_elapsed:.0f}秒")

        # 重新读取DB，获取ASR完成的数据
        fresh_posts = []
        for p in new_posts:
            fresh = repo.get_post(db.conn, p.post_id)
            if fresh and fresh.transcribed_text:
                fresh_posts.append(fresh)

        if fresh_posts:
            logger.info(f"ASR成功: {len(fresh_posts)}/{len(new_posts)} 条，开始AI整理...")
            ai_start = time.time()
            await orch._run_ai_pipeline(db, repo, fresh_posts)
            ai_elapsed = time.time() - ai_start
            logger.info(f"AI整理完成，耗时 {ai_elapsed:.0f}秒")

        # 统计成功数
        success_count = 0
        for p in new_posts:
            p2 = repo.get_post(db.conn, p.post_id)
            if p2 and (p2.ai_refined_text or p2.transcribed_text):
                success_count += 1

        orch.run_log.posts_new = len(new_posts)
        orch.run_log.posts_collected = len(posts)

    # ── 5. 导出 ──
    print("\n导出中...")
    try:
        result = subprocess.run([sys.executable, "export_results.py"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"导出出错: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("导出超时")

    # ── 完成 ──
    total_time = time.time() - start_time
    failed = len(new_posts) - success_count

    print(f"\n{'='*50}")
    print(f"✅ {target_name} 处理完成")
    print(f"   请求: {max_count} 条")
    print(f"   采集: {len(posts)} 条")
    print(f"   新增: {len(new_posts)} 条")
    print(f"   成功: {success_count} 条")
    if failed:
        print(f"   失败: {failed} 条（下载/ASR失败，下次自动重试）")
    print(f"   耗时: {total_time:.0f}秒 ({total_time/60:.1f}分钟)")
    print(f"{'='*50}")
    print(f"\n桌面查看: Desktop/抖音文案采集/文案/")


if __name__ == "__main__":
    asyncio.run(main())
