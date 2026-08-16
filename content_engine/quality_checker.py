"""质量检测器 - 文本相似度 + 规则检测"""
from difflib import SequenceMatcher
from loguru import logger


class QualityChecker:
    SIMILARITY_THRESHOLD = 0.75
    LENGTH_RATIO_MIN = 0.70
    LENGTH_RATIO_MAX = 1.30

    def check(self, original: str, rewritten: str) -> tuple[str, bool]:
        if not rewritten or rewritten == original:
            return original, True
        similarity = SequenceMatcher(None, original, rewritten).ratio()
        len_ratio = len(rewritten) / max(len(original), 1)
        if similarity < self.SIMILARITY_THRESHOLD:
            logger.warning(f"[质检] 相似度 {similarity:.0%}，退回原文")
            return original, False
        if len_ratio < self.LENGTH_RATIO_MIN or len_ratio > self.LENGTH_RATIO_MAX:
            logger.warning(f"[质检] 长度变化 {len_ratio:.0%}，退回原文")
            return original, False
        logger.info(f"[质检] 通过 (相似度 {similarity:.0%})")
        return rewritten, True
