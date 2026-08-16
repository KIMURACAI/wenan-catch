"""
抖音登录管理 - 扫码登录 + Cookie 持久化

流程:
1. 打开抖音首页，点击登录按钮
2. 切换到二维码登录模式
3. 用户用抖音 App 扫码
4. 自动检测登录成功，保存 Cookie
"""
from pathlib import Path

from loguru import logger
from playwright.async_api import BrowserContext, TimeoutError as PlaywrightTimeout
from browser.navigator import PageNavigator

from config import settings


class LoginManager:
    """抖音登录管理器"""

    def __init__(self, context: BrowserContext):
        self.context = context

    async def login_via_qrcode(self) -> bool:
        """
        通过二维码扫码登录

        先打开抖音首页 → 找登录按钮 → 切到二维码 → 扫码
        """
        page = await self.context.new_page()
        nav = PageNavigator()
        try:
            # 1. 打开首页
            logger.info("正在打开抖音首页...")
            await page.goto(
                settings.douyin_base_url,
                timeout=30000,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(3000)

            # 2. 尝试点击登录按钮
            logger.info("正在打开登录面板...")
            login_btns = [
                'span:has-text("登录")',
                '[class*="login"] button',
                '[class*="login"] span',
                '#login-btn',
            ]
            clicked = False
            for selector in login_btns:
                try:
                    btn = await page.query_selector(selector)
                    if btn:
                        await btn.click()
                        logger.info(f"已点击登录按钮: {selector}")
                        clicked = True
                        break
                except Exception:
                    continue

            if not clicked:
                logger.warning("未找到登录按钮，可能已登录")

            await page.wait_for_timeout(3000)

            # 3. 查找二维码
            logger.info("等待二维码加载...")
            qr_selectors = [
                'img[class*="qrcode"]',
                'img[alt*="扫码"]',
                'canvas[class*="qrcode"]',
                '.qrcode-img img',
                '[class*="QrCode"]',
            ]

            qr_found = False
            for selector in qr_selectors:
                try:
                    qr = await page.wait_for_selector(selector, timeout=3000)
                    if qr:
                        qr_found = True
                        break
                except Exception:
                    continue

            if not qr_found:
                # 可能需要在登录面板里切换到二维码tab
                qr_tabs = [
                    '[class*="scan"]',
                    '[class*="qrcode"]',
                    'div:has-text("扫码")',
                    '[class*="tab"]:has-text("二维码")',
                ]
                for tab_sel in qr_tabs:
                    try:
                        tab = await page.query_selector(tab_sel)
                        if tab:
                            await tab.click()
                            await page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue

            logger.info("二维码已加载，请用抖音 App 扫码登录")
            logger.info("等待扫码...（最长等待 2 分钟）")

            # 截图二维码方便扫码
            qr_path = Path(settings.data_dir) / "qrcode.png"
            qr_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                await page.screenshot(path=str(qr_path))
                logger.info(f"登录页面截图已保存到: {qr_path}")
            except Exception:
                pass

            # 4. 等待登录成功
            logged_selectors = [
                '[class*="avatar"]',
                '[class*="user-info"]',
                '[class*="Avatar"]',
            ]
            for selector in logged_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=120000)
                    logger.info("✅ 扫码登录成功！")
                    return True
                except PlaywrightTimeout:
                    continue

            logger.error("❌ 扫码登录超时（2分钟），请重试")
            return False

        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            return False
        finally:
            await page.close()
