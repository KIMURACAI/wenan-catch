"""
页面导航助手 - 提供人性化的页面交互模式

模拟真实用户的滚动、等待、点击等行为，降低被检测风险。
"""
import asyncio
import random
from typing import Optional

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout


class PageNavigator:
    """页面导航助手"""

    @staticmethod
    async def scroll_to_load(
        page: Page,
        max_attempts: int = 15,
        pause: float = 2.0,
        min_scroll: int = 300,
        max_scroll: int = 700,
        min_delay: float = 0.3,
        max_delay: float = 0.8,
    ) -> int:
        """
        模拟人性化滚动来加载更多内容

        Args:
            page: Playwright 页面对象
            max_attempts: 最大滚动次数
            pause: 每次滚动后的等待时间
            min_scroll: 最小滚动像素
            max_scroll: 最大滚动像素
            min_delay: 每次滚动间的最小延迟
            max_delay: 每次滚动间的最大延迟

        Returns:
            实际滚动次数
        """
        scroll_count = 0
        previous_height = 0

        for i in range(max_attempts):
            # 获取当前页面高度
            current_height = await page.evaluate("document.body.scrollHeight")

            if current_height == previous_height and i > 3:
                logger.debug(f"页面高度未变化，停止滚动 (第 {i+1} 次)")
                break

            previous_height = current_height

            # 分 3 次小步滚动，模拟人眼阅读节奏
            for _ in range(3):
                scroll_px = random.randint(min_scroll, max_scroll)
                await page.evaluate(f"window.scrollBy(0, {scroll_px})")
                await asyncio.sleep(random.uniform(min_delay, max_delay))

            # 主等待时间（等待新内容加载）
            await asyncio.sleep(pause)
            scroll_count += 1

        logger.debug(f"页面滚动完成，共滚动 {scroll_count} 次")
        return scroll_count

    @staticmethod
    async def safe_wait_for_text(
        page: Page,
        selector: str,
        timeout: int = 5000,
    ) -> Optional[str]:
        """
        安全地等待元素出现并获取文本

        Args:
            page: Playwright 页面对象
            selector: CSS 选择器
            timeout: 超时毫秒数

        Returns:
            元素的文本内容，如果未找到则返回 None
        """
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            if element:
                text = await element.inner_text()
                return text.strip() if text else None
            return None
        except (PlaywrightTimeout, Exception):
            return None

    @staticmethod
    async def safe_wait_for_attribute(
        page: Page,
        selector: str,
        attribute: str,
        timeout: int = 5000,
    ) -> Optional[str]:
        """安全地等待元素出现并获取属性"""
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            if element:
                return await element.get_attribute(attribute)
            return None
        except (PlaywrightTimeout, Exception):
            return None

    @staticmethod
    async def human_like_click(page: Page, selector: str):
        """
        模拟人类点击（先移动鼠标，再点击）
        """
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                box = await element.bounding_box()
                if box:
                    # 在元素范围内随机偏移点击位置
                    x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
                    y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
                    await page.mouse.move(x, y, steps=random.randint(5, 10))
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await page.mouse.click(x, y)
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    async def wait_for_page_settle(page: Page, timeout: int = 10000):
        """
        等待页面稳定（网络请求基本停止 + 渲染完成）
        """
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            # networkidle 可能超时，不影响
            pass
        await asyncio.sleep(random.uniform(0.5, 1.5))
