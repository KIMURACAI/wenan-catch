"""
话题页面采集器

访问抖音话题/挑战页面，通过 API 拦截获取该话题下的视频文案。
"""
import asyncio
from typing import Optional

from loguru import logger
from playwright.async_api import BrowserContext

from config import settings
from browser.navigator import PageNavigator
from models.schemas import Post, ScrapeTarget, TargetType
from .interceptor import APIInterceptor


class HashtagExtractor:
    """话题页面视频采集器"""

    def __init__(self, context: BrowserContext):
        self.context = context
        self.navigator = PageNavigator()

    async def extract(
        self,
        target: ScrapeTarget,
        max_videos: int = 20,
    ) -> list[Post]:
        """
        采集指定话题下的最新视频文案

        Args:
            target: 采集目标（话题）
            max_videos: 最多采集数量

        Returns:
            视频列表
        """
        logger.info(f"开始采集话题: {target.name} (hashtag_id: {target.douyin_id})")

        interceptor = APIInterceptor(
            source_target=target.name,
            source_type=TargetType.HASHTAG,
        )

        page = await self.context.new_page()
        try:
            # 注册 API 拦截器
            page.on("response", interceptor.intercept_response)

            # 导航到话题页
            url = settings.douyin_hashtag_url_template.format(
                hashtag_id=target.douyin_id
            )
            logger.info(f"正在访问: {url}")
            await page.goto(
                url,
                timeout=settings.douyin_page_timeout * 1000,
                wait_until="domcontentloaded",
            )
            await self.navigator.wait_for_page_settle(page)

            # 等待视频列表加载
            await asyncio.sleep(3)

            # 滚动加载更多
            scroll_count = await self.navigator.scroll_to_load(
                page,
                max_attempts=settings.douyin_max_scroll,
                pause=settings.douyin_scroll_pause,
                min_scroll=settings.douyin_min_scroll_px,
                max_scroll=settings.douyin_max_scroll_px,
                min_delay=settings.douyin_min_delay,
                max_delay=settings.douyin_max_delay,
            )

            # 额外等待，确保所有 API 响应已返回
            await asyncio.sleep(2)

            # 提取数据
            posts = await interceptor.extract_posts()
            posts = posts[:max_videos]

            logger.info(
                f"话题 {target.name} 采集完成: "
                f"共获取 {len(posts)} 条视频"
            )
            return posts

        except Exception as e:
            logger.error(f"采集话题 {target.name} 失败: {e}")
            return []
        finally:
            await page.close()
