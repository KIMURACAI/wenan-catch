"""
视频下载器 - 从抖音下载视频文件

支持缓存:
  cache/videos/  - 视频文件缓存
  cache/audios/  - 音频文件缓存

流程:
  1. 检查 cache/videos/{post_id}.mp4 是否存在
  2. 存在 -> 直接使用
  3. 不存在 -> 下载并缓存
"""
import asyncio
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from config import settings
from utils.exceptions import DownloadError


class VideoDownloader:
    """抖音视频下载器（带缓存）"""

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        temp_dir: Optional[str] = None,
    ):
        """
        Args:
            cache_dir: 视频缓存目录（默认 cache/videos/）
            temp_dir: 临时下载目录（默认 data/temp_videos/）
        """
        project_root = Path(settings.project_root)

        # 缓存目录
        cache_base = Path(cache_dir) if cache_dir else (project_root / "cache" / "videos")
        cache_base.mkdir(parents=True, exist_ok=True)
        self.cache_dir = cache_base

        # 临时目录
        temp_base = Path(temp_dir or settings.transcriber_temp_dir)
        temp_base.mkdir(parents=True, exist_ok=True)
        self.temp_dir = temp_base

        # 音频缓存
        audio_cache = project_root / "cache" / "audios"
        audio_cache.mkdir(parents=True, exist_ok=True)
        self.audio_cache_dir = audio_cache

    def get_cached_video(self, post_id: str) -> Optional[Path]:
        """获取缓存的视频文件"""
        path = self.cache_dir / f"{post_id}.mp4"
        if path.exists():
            logger.debug(f"视频缓存命中: {path.name}")
            return path
        return None

    def get_cached_audio(self, post_id: str) -> Optional[Path]:
        """获取缓存的音频文件"""
        path = self.audio_cache_dir / f"{post_id}.wav"
        if path.exists():
            logger.debug(f"音频缓存命中: {path.name}")
            return path
        return None

    def _video_paths(self, post_id: str) -> tuple[Path, Path]:
        """返回 (缓存路径, 临时路径)"""
        return (
            self.cache_dir / f"{post_id}.mp4",
            self.temp_dir / f"{post_id}.mp4",
        )

    async def download(
        self,
        video_urls: list[str] | str,
        post_id: str,
        use_cache: bool = True,
    ) -> Optional[Path]:
        """
        下载单个视频（自动使用缓存）

        Args:
            video_urls: 一个或多个视频播放地址
            post_id: 视频 ID
            use_cache: 是否启用缓存

        Returns:
            视频文件路径
        """
        if isinstance(video_urls, str):
            video_urls = [video_urls]

        if not video_urls:
            raise DownloadError(f"视频 {post_id} 没有播放地址")

        cache_path, temp_path = self._video_paths(post_id)

        # 1. 检查缓存
        if use_cache:
            cached = self.get_cached_video(post_id)
            if cached:
                return cached

        # 2. 下载
        if temp_path.exists():
            logger.debug(f"临时文件已存在: {temp_path.name}")
        else:
            headers = {
                "User-Agent": settings.stealth_user_agent,
                "Referer": "https://www.douyin.com/",
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }

            best_data = b""
            best_size = 0
            checked = 0

            for idx, url in enumerate(video_urls):
                url = url.replace("playwm", "play")
                try:
                    checked += 1
                    logger.info(
                        f"正在下载 {post_id} (尝试 {idx+1}/{len(video_urls)})..."
                    )
                    async with httpx.AsyncClient(
                        follow_redirects=True, timeout=15.0, headers=headers
                    ) as client:
                        resp = await client.get(url)
                        if resp.status_code in (200, 206) and len(resp.content) > best_size:
                            best_data = resp.content
                            best_size = len(resp.content)
                            # 只要找到一个可用的就直接用，不继续试了
                            if best_size > 1024 * 500:  # >500KB 认为够用
                                break
                except Exception as e:
                    logger.debug(f"URL {idx+1} 下载失败: {e}")
                    continue

            if not best_data:
                raise DownloadError(f"视频 {post_id} 所有 URL 下载失败")

            temp_path.write_bytes(best_data)
            file_mb = best_size / (1024 * 1024)
            logger.info(f"视频 {post_id} 下载完成 ({file_mb:.1f} MB)")

        # 3. 缓存: 复制到 cache/videos/
        if use_cache and temp_path.exists() and not cache_path.exists():
            import shutil
            shutil.copy2(temp_path, cache_path)
            logger.debug(f"已缓存到: {cache_path.name}")

        return temp_path

    def cache_audio(self, post_id: str, audio_path: Path) -> Path:
        """
        缓存音频文件到 cache/audios/

        Args:
            post_id: 视频 ID
            audio_path: 当前音频路径

        Returns:
            缓存后的音频路径
        """
        cached = self.audio_cache_dir / f"{post_id}.wav"
        if not cached.exists() and audio_path.exists():
            import shutil
            shutil.copy2(audio_path, cached)
            logger.debug(f"音频已缓存: {cached.name}")
        return cached

    async def cleanup(self, post_id: str):
        """清理临时文件（保留缓存）"""
        temp_video = self.temp_dir / f"{post_id}.mp4"
        temp_audio = self.temp_dir / f"{post_id}.wav"
        if temp_video.exists():
            temp_video.unlink()
        if temp_audio.exists():
            temp_audio.unlink()

    async def cleanup_all(self):
        """清理所有临时文件"""
        for f in self.temp_dir.glob("*"):
            if f.is_file():
                f.unlink()
