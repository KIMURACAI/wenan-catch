"""
抖音文案采集系统 - 主入口

提供三种运行模式:
  once:   执行一次完整采集 (用于定时任务)
  login:  抖音扫码登录，保存 Cookie
  daemon: 常驻进程模式 (调试用)

用法:
  python main.py --mode once
  python main.py --mode login
  python main.py --mode daemon
  python main.py --mode once --no-transcribe  # 跳过语音转文字
  python main.py --mode once --ai-refine      # 启用 AI 润色
  python main.py --mode once --dry-run        # 试运行（不写飞书）
"""
import argparse
import asyncio
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from loguru import logger

from config import settings
from browser.manager import BrowserManager
from browser.login import LoginManager


def setup_logging():
    """配置日志系统"""
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 移除默认的日志处理器
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:^7}</level> | <cyan>{message}</cyan>",
        colorize=True,
    )

    # 文件输出（按天轮转，保留 7 天）
    logger.add(
        log_dir / "wenan_catch_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="00:00",
        retention=7,
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:^7} | {name}:{function}:{line} | {message}",
    )


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="抖音文案采集系统 - 自动采集抖音视频文案并生成飞书日报",
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="once",
        choices=["once", "login", "daemon"],
        help="运行模式: once=单次采集, login=登录, daemon=守护进程",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="使用无头浏览器（默认开启）",
    )

    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="显示浏览器界面（用于调试）",
    )

    parser.add_argument(
        "--no-transcribe",
        action="store_true",
        help="跳过语音转文字步骤",
    )

    parser.add_argument(
        "--ai-refine",
        action="store_true",
        help="启用 AI 润色（调用 DeepSeek 润色文案）",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式（不写入飞书）",
    )

    return parser.parse_args()


async def run_once(args):
    """执行一次完整采集"""
    logger.info("启动单次采集模式")

    from pipeline.orchestrator import Orchestrator

    orchestrator = Orchestrator(
        headless=args.headless,
        enable_transcribe=not args.no_transcribe,
        enable_ai_refine=args.ai_refine,
        dry_run=args.dry_run,
    )

    await orchestrator.run()


async def run_login(args):
    """抖音扫码登录"""
    logger.info("启动登录模式")
    logger.info("=" * 50)
    logger.info("请在弹出的浏览器窗口中用抖音 App 扫码登录")
    logger.info("=" * 50)

    async with BrowserManager(headless=False) as browser:
        context = await browser.create_context(load_cookies=False)

        login_manager = LoginManager(context)
        success = await login_manager.login_via_qrcode()

        if success:
            # 保存 Cookie
            await browser.save_cookies(context)
            logger.info("✅ 登录成功，Cookie 已保存")
        else:
            logger.error("❌ 登录失败")
            sys.exit(1)


async def run_daemon(args):
    """守护进程模式（调试用）"""
    logger.info("启动守护进程模式")

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error("请先安装 APScheduler: pip install APScheduler")
        sys.exit(1)

    # 解析运行时间
    run_time = settings.daily_run_time
    hour, minute = run_time.split(":")
    logger.info(f"定时任务已设置: 每天 {hour}:{minute} 执行")

    scheduler = AsyncIOScheduler()

    async def run_once_async():
        await run_once(args)

    scheduler.add_job(
        run_once_async,
        trigger=CronTrigger(hour=int(hour), minute=int(minute)),
        id="daily_scrape",
        misfire_grace_time=3600,
        name="抖音文案每日采集",
    )

    # 启动后立即执行一次
    logger.info("首次启动，立即执行一次采集...")
    await run_once(args)

    # 进入调度循环
    scheduler.start()
    logger.info("调度器已启动，等待下次执行...")

    try:
        # 保持运行
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("收到退出信号")
        scheduler.shutdown()


def main():
    """主入口"""
    args = parse_args()
    setup_logging()

    logger.info(f"抖音文案采集系统 v1.0")
    logger.info(f"工作目录: {settings.project_root}")
    logger.info(f"数据目录: {settings.data_dir}")
    logger.info(f"日志级别: {settings.log_level}")

    # 执行对应模式
    if args.mode == "once":
        asyncio.run(run_once(args))
    elif args.mode == "login":
        asyncio.run(run_login(args))
    elif args.mode == "daemon":
        asyncio.run(run_daemon(args))


if __name__ == "__main__":
    main()
