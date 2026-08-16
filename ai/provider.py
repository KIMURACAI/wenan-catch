"""
AI 提供者 - DeepSeek API 调用
同步: call() | 异步: call_async() | 润色: rewrite()
"""
from typing import Optional

import httpx
from loguru import logger

from utils.exceptions import AIError
from .prompt_loader import load_prompt


class AIProvider:
    """AI 提供者"""

    API_BASE = "https://api.deepseek.com/v1"
    MODEL = "deepseek-chat"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()
        self._system_prompt = load_prompt("rewrite")

    def _get_api_key(self) -> str:
        from config import settings
        key = getattr(settings, "deepseek_api_key", "")
        if not key:
            import os
            key = os.environ.get("DEEPSEEK_API_KEY", "")
        return key

    # ── 同步调用（兼容旧代码，会阻塞事件循环） ──

    def call(self, messages: list[dict], timeout: int = 60) -> str:
        """同步调用 LLM API（阻塞事件循环，旧代码兼容）"""
        if not self.api_key:
            raise AIError("DeepSeek API Key 未配置")
        try:
            resp = httpx.post(
                f"{self.API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 2048},
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except httpx.TimeoutException:
            raise AIError("API 请求超时")
        except httpx.HTTPStatusError as e:
            raise AIError(f"API 请求失败: {e.response.status_code}")
        except (KeyError, IndexError, ValueError) as e:
            raise AIError(f"API 返回格式异常: {e}")
        except Exception as e:
            raise AIError(f"API 调用异常: {e}")

    # ── 异步调用（推荐，不阻塞事件循环） ──

    async def call_async(self, messages: list[dict], timeout: int = 60) -> str:
        """异步调用 LLM API"""
        if not self.api_key:
            raise AIError("DeepSeek API Key 未配置")
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{self.API_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"model": self.MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 2048},
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
        except httpx.TimeoutException:
            raise AIError("API 请求超时")
        except httpx.HTTPStatusError as e:
            raise AIError(f"API 请求失败: {e.response.status_code}")
        except (KeyError, IndexError, ValueError) as e:
            raise AIError(f"API 返回格式异常: {e}")
        except Exception as e:
            raise AIError(f"API 调用异常: {e}")

    # ── 润色（异步，不阻塞） ──

    async def rewrite(self, text: str, source: str = "") -> str:
        """润色文案"""
        if not text or len(text.strip()) < 5:
            return text
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": f"来源：{source}\n\n{text}" if source else text},
        ]
        try:
            result = await self.call_async(messages)
            logger.info(f"[AI] 润色完成 ({len(result)}字)")
            return result
        except AIError as e:
            logger.warning(f"[AI] 润色失败: {e}")
            return text
