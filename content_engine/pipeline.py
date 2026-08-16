"""Content Engine 总控

流程: ASR文本 → AI整理 → 过改检测 → 输出
"""
import time
from dataclasses import dataclass
from loguru import logger
from ai.provider import AIProvider
from .rewriter import ContentRewriter
from .quality_checker import QualityChecker


@dataclass
class ContentEngineResult:
    refined_text: str
    modified: bool = False
    error: str = ""
    processing_time: float = 0.0


class ContentEnginePipeline:
    def __init__(self, ai_provider: AIProvider):
        self.rewriter = ContentRewriter(ai_provider)
        self.quality_checker = QualityChecker()

    async def process(self, text: str, source: str = "") -> ContentEngineResult:
        start = time.time()
        if not text or len(text.strip()) < 5:
            return ContentEngineResult(refined_text=text, processing_time=time.time() - start)

        result = ContentEngineResult(refined_text=text)
        logger.info(f"[CE] 整理 ({len(text)}字)")

        # AI整理
        try:
            rewritten = await self.rewriter.rewrite(text, source)
            if rewritten != text:
                result.modified = True
                result.refined_text = rewritten
        except Exception as e:
            logger.warning(f"[CE] 整理失败: {e}")

        # 过改检测（纯规则）
        if result.modified:
            checked, ok = self.quality_checker.check(text, result.refined_text)
            result.refined_text = checked
            if not ok:
                result.modified = False

        result.processing_time = time.time() - start
        return result
