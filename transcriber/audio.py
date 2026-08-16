"""
音频提取器 - 从视频文件中提取音频

使用 ffmpeg 将视频的音频轨道提取为 WAV 格式，
供 Whisper 进行语音识别。
"""
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger


class AudioExtractor:
    """视频音频提取器"""

    # ffmpeg 可能的安装位置
    FFMPEG_CANDIDATES = [
        "ffmpeg",
        # ffmpeg-downloader 安装路径
        str(Path.home() / "AppData" / "Local" / "ffmpegio" / "ffmpeg-downloader" / "ffmpeg" / "bin" / "ffmpeg.exe"),
        # 项目自带
        str(Path(__file__).resolve().parent.parent / "ffmpeg.exe"),
        # 系统安装
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe",
        # Playwright 自带的 ffmpeg
        str(Path.home() / "AppData" / "Local" / "ms-playwright" / "ffmpeg-1011" / "ffmpeg-win64.exe"),
    ]

    def __init__(self, ffmpeg_path: Optional[str] = None):
        """
        Args:
            ffmpeg_path: ffmpeg 可执行文件路径。
                         None 则自动查找。
        """
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
        if not self.ffmpeg_path:
            logger.warning(
                "未找到 ffmpeg！请安装 ffmpeg 并将其加入 PATH，"
                "或在 settings 中指定路径。"
            )

    def _find_ffmpeg(self) -> Optional[str]:
        """自动查找 ffmpeg 可执行文件"""
        for candidate in self.FFMPEG_CANDIDATES:
            try:
                result = subprocess.run(
                    [candidate, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    logger.debug(f"找到 ffmpeg: {candidate}")
                    return candidate
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def extract_audio(self, video_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径（默认同目录下的 WAV）

        Returns:
            音频文件路径，失败返回 None
        """
        if not self.ffmpeg_path:
            logger.error("ffmpeg 不可用，无法提取音频")
            return None

        if not video_path.exists():
            logger.error(f"视频文件不存在: {video_path}")
            return None

        if output_path is None:
            output_path = video_path.with_suffix(".wav")

        # 如果音频已存在，跳过
        if output_path.exists():
            logger.debug(f"音频已存在: {output_path}")
            return output_path

        try:
            logger.info(f"正在提取音频: {video_path.name}")

            # 使用 ffmpeg 提取音频为 16kHz 单声道 WAV（Whisper 最佳输入格式）
            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),       # 输入文件
                "-vn",                         # 无视频
                "-acodec", "pcm_s16le",        # PCM 16-bit
                "-ar", "16000",                # 16kHz 采样率
                "-ac", "1",                    # 单声道
                "-y",                          # 覆盖输出
                str(output_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
            )

            if result.returncode == 0:
                file_size = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"音频提取完成: {output_path.name} ({file_size:.1f} MB)")
                return output_path
            else:
                logger.error(f"音频提取失败: {result.stderr[:200]}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"音频提取超时: {video_path.name}")
            return None
        except Exception as e:
            logger.error(f"音频提取出错: {e}")
            return None

    @property
    def is_available(self) -> bool:
        """ffmpeg 是否可用"""
        return self.ffmpeg_path is not None
