"""
抖音 API 响应拦截器

核心策略：拦截抖音页面加载时内部 API 返回的 JSON 数据，
从中提取视频文案、作者、时间等信息。

优势：相比解析 DOM，API 响应结构更稳定，字段更完整。
"""
import json
from datetime import datetime, timezone
from typing import Callable, Optional

from loguru import logger
from playwright.async_api import Page, Response

from models.schemas import Post, TargetType, TaskStatus


class APIInterceptor:
    """
    拦截抖音内部 API 响应并解析为结构化数据

    使用方式:
        interceptor = APIInterceptor(target_name="张三", target_type="user")
        page.on("response", interceptor.intercept_response)
        # ... 导航到目标页面 ...
        posts = interceptor.extract_posts()
    """

    # 抖音内部 API 路径特征（相对稳定）
    API_PATTERNS = [
        "/aweme/v1/web/aweme/post/",         # 用户作品列表
        "/aweme/v1/web/aweme/feed/",         # 推荐/话题 Feed
        "/aweme/v1/web/aweme/detail/",       # 单个视频详情
        "/aweme/v1/web/general/search/single/",  # 搜索结果
        "/aweme/v1/web/aweme/listcollection/",   # 收藏列表
    ]

    def __init__(
        self,
        source_target: str = "",
        source_type: TargetType = TargetType.USER,
        on_post_found: Optional[Callable[[dict], None]] = None,
    ):
        """
        Args:
            source_target: 来源目标名称（如 "张三"）
            source_type: 来源类型（user 或 hashtag）
            on_post_found: 可选回调，每发现一条新视频时调用
        """
        self.source_target = source_target
        self.source_type = source_type
        self.on_post_found = on_post_found
        self._raw_responses: list[dict] = []
        self._captured_posts: list[dict] = []
        self._seen_post_ids: set[str] = set()

    async def intercept_response(self, response: Response):
        """
        拦截响应的回调函数

        直接传给 page.on("response", ...) 使用
        """
        url = response.url

        # 只关注抖音内部 API
        if not any(pattern in url for pattern in self.API_PATTERNS):
            return

        try:
            body = await response.json()
            self._raw_responses.append(body)

            aweme_list = body.get("aweme_list", [])
            if not aweme_list:
                return

            for item in aweme_list:
                post = self._parse_aweme_item(item)
                if post and post["aweme_id"] not in self._seen_post_ids:
                    self._seen_post_ids.add(post["aweme_id"])
                    self._captured_posts.append(post)
                    if self.on_post_found:
                        self.on_post_found(post)

            logger.debug(f"拦截到 {len(aweme_list)} 条视频数据 (累计 {len(self._captured_posts)} 条)")

        except (json.JSONDecodeError, Exception) as e:
            # 非 JSON 响应或解析错误，忽略
            pass

    def _parse_aweme_item(self, item: dict) -> Optional[dict]:
        """解析单条抖音视频数据
        
        从 API 响应中提取所有可用文本: desc(描述)、subtitle(字幕)
        优先使用字幕（如果有的话，比 desc 更准确）
        """
        try:
            aweme_id = str(item.get("aweme_id", ""))
            if not aweme_id:
                return None

            author = item.get("author", {}) or {}

            # 获取视频播放地址
            video_info = item.get("video", {}) or {}
            play_addr = video_info.get("play_addr", {}) or {}
            url_list = play_addr.get("url_list", [])
            # 有些接口用 bit_rate 结构
            bit_rates = video_info.get("bit_rate", []) or []
            for br in bit_rates:
                br_addr = (br.get("play_addr", {}) or {}).get("url_list", [])
                url_list.extend(br_addr)
            duration = video_info.get("duration", 0)  # 毫秒

            # 获取文案描述
            desc = item.get("desc", "") or ""

            # 获取分享标题

            share_info = item.get("share_info", {}) or {}
            share_title = share_info.get("share_title", "") or ""

            # 获取话题标签
            text_extra = item.get("text_extra", []) or []
            hashtags = [
                t["hashtag_name"]
                for t in text_extra
                if t.get("hashtag_name")
            ]

            # 创建时间
            create_time = item.get("create_time")
            publish_time = None
            if create_time:
                publish_time = datetime.fromtimestamp(create_time, tz=timezone.utc)

            return {
                "aweme_id": aweme_id,
                "desc": desc,
                "share_title": share_title,
                "author_uid": str(author.get("uid", "")),
                "author_nickname": author.get("nickname", "") or "",
                "author_unique_id": author.get("unique_id", "") or "",
                "create_time": create_time,
                "publish_time": publish_time,
                "video_url": url_list[0] if url_list else "",
                "video_url_list": url_list,
                "hashtags": hashtags,
                "is_ad": item.get("is_ad", False),
                "music": item.get("music", {}),
                "statistics": item.get("statistics", {}),
            }
        except Exception as e:
            logger.warning(f"解析视频数据失败: {e}")
            return None

    @staticmethod
    def _has_real_text(desc: str) -> bool:
        """
        判断 desc 中是否包含"真正的文案"

        策略（按优先级）:
        1. 空文本 → False
        2. 只包含话题标签（#书法#国画）→ False
        3. 文本看起来是乱码/无意义 → False（触发语音转文字）
        4. 至少有 4 个中文字符 → True
        """
        if not desc:
            return False

        import re
        cleaned = re.sub(r'#\S+', '', desc)
        cleaned = re.sub(r'@\S+', '', cleaned)
        cleaned = re.sub(r'https?://\S+', '', cleaned)
        cleaned = cleaned.strip().strip('#@，。！？：；,.:;!? ')

        # 至少需要 4 个中文字符才考虑
        if len(cleaned) < 4:
            return False

        # ── 乱码检测 ──
        # 抖音 API 偶尔返回的 desc 是 OCR 错误的乱码
        # 这些乱码通常有混合脚本（中英混+俄语/韩语）
        
        # 1) 中文比例检测
        chinese_chars = sum(1 for c in cleaned if '\u4e00' <= c <= '\u9fff')
        total_real = len(cleaned.replace(' ', ''))
        if total_real > 0 and chinese_chars / total_real < 0.6:
            return False

        # 2) 重复字符检测（"字幕字幕字幕字幕"）
        if len(cleaned) >= 8:
            for w in [2, 3]:
                seen = {}
                for i in range(len(cleaned) - w + 1):
                    chunk = cleaned[i:i+w]
                    seen[chunk] = seen.get(chunk, 0) + 1
                if any(c >= 4 for c in seen.values()):
                    return False

        # 3) 混合非正常字符检测（俄语、韩语、特殊符号等）
        suspect_count = 0
        for c in cleaned:
            is_normal = (
                ('\u4e00' <= c <= '\u9fff') or
                ('a' <= c <= 'z') or ('A' <= c <= 'Z') or
                ('0' <= c <= '9') or
                c in '，。、！？：；""''（）【】《》—…·～'
            )
            if not is_normal:
                suspect_count += 1
        if total_real > 0 and suspect_count / total_real > 0.1:
            return False

        return True

    async def extract_posts(self) -> list[Post]:
        """将拦截到的原始数据转换为 Post 模型列表"""
        posts = []
        for raw in self._captured_posts:
            raw_desc = (raw["desc"] or "").strip()

            # ── 全部走语音转文字 ──
            # 不管有没有字幕、有没有页面文案，全部走 ASR + AI 整理
            # 页面文案保留在 video_desc 中仅作参考
            need_transcribe = True

            post = Post(
                post_id=raw["aweme_id"],
                author_name=raw["author_nickname"],
                author_id=raw["author_uid"],
                video_desc=raw_desc,
                video_title=raw["share_title"],
                publish_time=raw["publish_time"],
                video_url=raw["video_url"],
                video_urls=raw["video_url_list"],
                hashtags=raw["hashtags"],
                source_target=self.source_target,
                source_type=self.source_type,
                task_status=(
                    TaskStatus.NEW if need_transcribe
                    else TaskStatus.DONE
                ),
            )
            posts.append(post)

        logger.info(
            f"共解析 {len(posts)} 条视频，"
            f"其中 {sum(1 for p in posts if p.task_status == TaskStatus.NEW)} 条需要语音转文字"
        )
        return posts

    @property
    def count(self) -> int:
        """拦截到的视频数量"""
        return len(self._captured_posts)

    def reset(self):
        """重置拦截器状态"""
        self._raw_responses.clear()
        self._captured_posts.clear()
        self._seen_post_ids.clear()
