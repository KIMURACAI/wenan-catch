"""
语音转文字引擎 - 使用 OpenAI Whisper 将音频转为中文文案

Whisper 模型大小对照:
- tiny: ~1GB VRAM, 速度快但准确率一般
- base: ~1GB VRAM, 速度/准确率平衡
- small: ~2GB VRAM, 推荐（有 NVIDIA 显卡）
- medium: ~5GB VRAM, 更准确（有 NVIDIA 显卡推荐）
- large-v3: ~10GB VRAM, 最准确

你的电脑有 NVIDIA 独显，推荐使用 medium 模型。
"""
from pathlib import Path
from typing import Optional

import os

# ═══════════════════════════════════════════════════════════════
# ★ 关键：在导入 whisper 之前先把 ffmpeg 加到 PATH
# Whisper 内部会通过 subprocess 调用 ffmpeg，找不到就会炸
# ═══════════════════════════════════════════════════════════════
_FFMPEG_CANDIDATES = [
    r"C:\Users\Kimura\AppData\Local\ffmpegio\ffmpeg-downloader\ffmpeg\bin",
]
for _dir in _FFMPEG_CANDIDATES:
    _exe = os.path.join(_dir, "ffmpeg.exe")
    if os.path.exists(_exe) and _dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _dir + os.pathsep + os.environ.get("PATH", "")
        break

import re
import whisper
import torch
from loguru import logger

from config import settings
from .downloader import VideoDownloader
from .audio import AudioExtractor


# ═══════════════════════════════════════════════════════════════
# 乱码/劣质文本检测（保护飞书不被垃圾文案污染）
# ═══════════════════════════════════════════════════════════════

def _is_garbled(text: str) -> bool:
    """
    判断文本是否为乱码/无意义转录
    
    检测策略:
    1. 中文比例过低 (< 50%) → 乱码
    2. 重复字符过多（如"字幕字幕字幕"）→ 乱码
    3. 混合非中文非拉丁字符（如俄语、韩语）→ 乱码
    4. 平均置信度过低 
    """
    if not text or len(text.strip()) < 2:
        return True

    # 1. 中文比例
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_chars = len(text.strip().replace(' ', ''))
    if total_chars > 0 and chinese_chars / total_chars < 0.5:
        return True

    # 2. 重复字符检测（连续相同子串过长）
    # 比如 "字幕字幕字幕字幕" 或 "敬禮敬禮敬禮"
    if len(text) >= 6:
        for window in [2, 3]:
            counts = {}
            for i in range(len(text) - window + 1):
                chunk = text[i:i+window]
                counts[chunk] = counts.get(chunk, 0) + 1
            # 同一个 2/3-gram 出现 >= 3 次 → 很可能是重复噪音
            if any(c >= 3 for c in counts.values()):
                return True

    # 3. 混合非中/英/日/韩字符（俄语、希腊语、特殊符号等）
    suspect_count = 0
    for c in text:
        cp = ord(c)
        # 非中文、非英文、非数字、非标点
        is_normal = (
            ('\u4e00' <= c <= '\u9fff') or  # 中文
            ('\u3040' <= c <= '\u30ff') or  # 日文
            ('\uac00' <= c <= '\ud7af') or  # 韩文
            ('a' <= c <= 'z') or ('A' <= c <= 'Z') or
            ('0' <= c <= '9') or
            c in '，。、！？：；""''（）【】《》—…·～,.!?:;"\'()[]{}<>-\'\u3000'  # 常见标点
        )
        if not is_normal:
            suspect_count += 1
    if total_chars > 0 and suspect_count / total_chars > 0.1:
        return True

    return False


def _is_acceptable_confidence(logprob: float) -> bool:
    """
    判断置信度是否可接受
    
    Whisper 的 avg_logprob 通常是负数
    - 优于 -0.5: 非常好的识别
    - -0.5 ~ -1.0: 合格
    - -1.0 ~ -2.0: 一般，可能有错字
    - 低于 -2.0: 大概率是乱码/噪音
    """
    return logprob >= -2.0


class WhisperTranscriber:
    """
    Whisper 语音转文字

    流程:
    1. 从视频 URL 下载视频
    2. 提取音频 (ffmpeg)
    3. 使用 Whisper 进行语音识别
    4. 返回转写文本
    """

    def __init__(
        self,
        model_size: str = "medium",
        language: str = "zh",
        device: Optional[str] = None,
    ):
        """
        Args:
            model_size: Whisper 模型大小
            language: 识别语言
            device: 运行设备 ("cuda" | "cpu")，None 自动检测
        """
        self.model_size = model_size
        self.language = language
        self.device = device or self._detect_device()
        self._model = None

    def _detect_device(self) -> str:
        """自动检测可用设备"""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"检测到 NVIDIA 显卡: {gpu_name}")
            return "cuda"
        else:
            logger.warning("未检测到 NVIDIA 显卡，使用 CPU 模式（速度较慢）")
            return "cpu"

    def _load_model(self):
        """加载 Whisper 模型（延迟加载）"""
        if self._model is not None:
            return

        logger.info(f"正在加载 Whisper {self.model_size} 模型 (device: {self.device})...")
        logger.info("首次加载会下载模型文件，请耐心等待...")

        try:
            self._model = whisper.load_model(
                self.model_size,
                device=self.device,
            )
            logger.info(f"Whisper {self.model_size} 模型加载完成")
        except Exception as e:
            logger.error(f"Whisper 模型加载失败: {e}")
            raise

    def transcribe(self, audio_path: Path) -> dict:
        """
        对音频文件进行语音识别

        Args:
            audio_path: 音频文件路径 (.wav)

        Returns:
            识别结果 dict:
            {
                "text": "完整转写文本",
                "segments": [...],
                "language": "zh"
            }
        """
        if not audio_path.exists():
            logger.error(f"音频文件不存在: {audio_path}")
            return {"text": "", "segments": [], "language": "zh"}

        self._load_model()

        logger.info(f"正在识别语音: {audio_path.name}...")

        try:
            result = self._model.transcribe(
                str(audio_path),
                language=self.language,
                task="transcribe",
                verbose=False,
                # 中文优化参数
                compression_ratio_threshold=2.0,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6,
                condition_on_previous_text=True,
            )

            text = result.get("text", "").strip()
            segments = result.get("segments", [])
            avg_confidence = (
                sum(s.get("avg_logprob", 0) for s in segments) / len(segments)
                if segments else None
            )

            # ── 多级过滤 ──
            should_discard = False
            discard_reason = ""

            # 1) 置信度过滤（主要防线）
            if avg_confidence is not None and not _is_acceptable_confidence(avg_confidence):
                should_discard = True
                discard_reason = f"置信度过低 ({avg_confidence:.2f})"

            # 2) 乱码检测
            if not should_discard and text and _is_garbled(text):
                should_discard = True
                discard_reason = "检测为乱码/无意义文本"

            # 3) 字数太少（< 5 字的短文本大概率是噪音/幻觉）
            if not should_discard and text and len(text) < 5:
                should_discard = True
                discard_reason = "字数太少 (< 5)"

            if should_discard:
                logger.warning(f"语音识别结果已丢弃 ({discard_reason}): {repr(text[:60])}")
                text = ""

            if text:
                logger.info(
                    f"语音识别完成: {len(text)} 字 (置信度: {avg_confidence:.2f})"
                )
            else:
                logger.warning(f"语音识别结果为空/已过滤: {audio_path.name}")

            return {
                "text": text,
                "segments": segments,
                "language": result.get("language", "zh"),
                "confidence": avg_confidence,
            }

        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return {"text": "", "segments": [], "language": "zh", "error": str(e)}

    async def process_video(
        self,
        video_url: str,
        post_id: str,
        cleanup: bool = True,
    ) -> tuple[str, Optional[float]]:
        """
        完整处理一条视频：下载 → 提取音频 → 语音识别

        Args:
            video_url: 视频播放地址
            post_id: 视频 ID
            cleanup: 是否清理临时文件

        Returns:
            (transcribed_text, confidence)
        """
        downloader = VideoDownloader()
        audio_extractor = AudioExtractor()

        # 1. 下载视频
        video_path = await downloader.download(video_url, post_id)
        if not video_path:
            return ("", None)

        # 2. 提取音频
        audio_path = audio_extractor.extract_audio(video_path)
        if not audio_path:
            if cleanup:
                await downloader.cleanup(post_id)
            return ("", None)

        # 3. 语音识别
        result = self.transcribe(audio_path)
        text = result.get("text", "")
        confidence = result.get("confidence")

        # 4. 清理临时文件
        if cleanup:
            await downloader.cleanup(post_id)
            # 如果音频不是和视频同一个文件，也清理音频
            if audio_path != video_path.with_suffix(".wav"):
                audio_path.unlink(missing_ok=True)

        return (text, confidence)


# ===== 快捷函数 =====

def transcribe_audio(audio_path: str, model_size: str = "medium") -> str:
    """
    快捷函数：对音频文件进行语音识别

    Args:
        audio_path: 音频文件路径
        model_size: Whisper 模型大小

    Returns:
        识别出的文字
    """
    transcriber = WhisperTranscriber(model_size=model_size)
    result = transcriber.transcribe(Path(audio_path))
    return result.get("text", "")
