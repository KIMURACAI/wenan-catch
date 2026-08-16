"""
浏览器管理器 - Playwright 生命周期管理

负责:
- 启动/关闭 Chromium 浏览器
- 创建浏览器上下文（含反检测、Cookie 加载）
- 提供统一的上下文管理器接口
"""
import json
from pathlib import Path
from typing import Optional

from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

from config import settings
from .anti_detect import apply_stealth_patches


class BrowserManager:
    """Playwright 浏览器生命周期管理器"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """启动 Playwright 和 Chromium 浏览器"""
        logger.info("正在启动浏览器...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-infobars",
                "--window-size=1920,1080",
            ],
        )
        logger.info(f"浏览器已启动 (headless={self.headless})")

    async def stop(self):
        """关闭浏览器和 Playwright"""
        if self._browser:
            await self._browser.close()
            logger.info("浏览器已关闭")
        if self._playwright:
            await self._playwright.stop()
            logger.info("Playwright 已停止")

    async def create_context(self, load_cookies: bool = True) -> BrowserContext:
        """
        创建浏览器上下文（相当于一个独立的浏览器会话）

        Args:
            load_cookies: 是否加载已保存的 Cookie

        Returns:
            配置好的 BrowserContext 实例
        """
        context = await self._browser.new_context(
            viewport={"width": settings.stealth_viewport_width,
                       "height": settings.stealth_viewport_height},
            user_agent=settings.stealth_user_agent,
            locale=settings.stealth_locale,
            timezone_id=settings.stealth_timezone,
            ignore_https_errors=True,
        )

        # 应用反检测脚本
        await apply_stealth_patches(context)

        # 加载已保存的 Cookie
        if load_cookies:
            await self._load_cookies(context)

        logger.debug("浏览器上下文已创建")
        return context

    async def _load_cookies(self, context: BrowserContext):
        """加载已持久化的 Cookie"""
        cookie_path = Path(settings.douyin_cookie_path)
        if cookie_path.exists():
            try:
                with open(cookie_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                if cookies:
                    await context.add_cookies(cookies)
                    logger.info(f"已加载 {len(cookies)} 条 Cookie")
            except Exception as e:
                logger.warning(f"Cookie 加载失败: {e}")

    async def save_cookies(self, context: BrowserContext):
        """保存当前上下文的 Cookie 到文件"""
        cookies = await context.cookies()
        cookie_path = Path(settings.douyin_cookie_path)
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cookie_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存 {len(cookies)} 条 Cookie 到 {cookie_path}")

    async def check_login_status(self, context: BrowserContext) -> bool:
        """
        检查抖音登录状态是否有效

        导航到抖音首页，通过检测登录后特有的元素（用户头像）来判断。
        比文本关键词匹配更可靠。
        """
        page = await context.new_page()
        try:
            await page.goto(
                f"{settings.douyin_base_url}/",
                timeout=settings.douyin_page_timeout * 1000,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(3000)

            # 检查登录态特征：用户头像或用户信息区域
            # 登录后页面会出现头像元素，未登录则跳到登录页
            current_url = page.url
            if "passport" in current_url or "login" in current_url:
                logger.warning("抖音登录状态已失效（被重定向到登录页）")
                return False

            # 检测登录后的典型元素（头像、用户信息）
            # 抖音未登录时不会有这些元素
            avatar_selectors = [
                'span[class*="avatar"]',
                '[class*="user-info"]',
                '[class*="Avatar"]',
            ]
            for selector in avatar_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info("抖音登录状态有效（检测到头像元素）")
                        return True
                except Exception:
                    continue

            # 兜底：检查 Cookie 是否包含登录凭证
            cookies = await context.cookies()
            session_cookies = [c for c in cookies if "session" in c["name"].lower()
                               or "sid" in c["name"].lower()
                               or "token" in c["name"].lower()]
            if session_cookies:
                logger.warning("登录状态不确定（有 Cookie 但无头像元素，可能过期）")
                return False

            logger.warning("抖音登录状态已失效")
            return False

        except Exception as e:
            logger.error(f"登录状态检查失败: {e}")
            return False
        finally:
            await page.close()
