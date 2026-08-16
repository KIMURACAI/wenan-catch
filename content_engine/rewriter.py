"""AI 整理器 - 极简文案整理"""
from loguru import logger
from ai.provider import AIProvider
from .prompt_loader import load_ce_prompt


class ContentRewriter:
    PROMPT_NAME = "rewrite"

    def __init__(self, ai_provider: AIProvider):
        self.provider = ai_provider
        self._prompt_template = load_ce_prompt(self.PROMPT_NAME)

    async def rewrite(self, text: str, source: str = "") -> str:
        if not text or len(text.strip()) < 5:
            return text
        messages = [
            {"role": "system", "content": self._prompt_template},
            {"role": "user", "content": f"来源：{source}\n\n{text[:1000]}" if source else text[:1000]},
        ]
        try:
            result = self.provider.call(messages, timeout=60).strip()
            if result and result != text:
                from difflib import SequenceMatcher
                ratio = SequenceMatcher(None, text, result).ratio()
                logger.info(f"[整理] 完成 ({len(result)}字, 保留率{ratio:.0%})")
                return result
            return text
        except Exception as e:
            logger.warning(f"[整理] 失败: {e}")
            return text
