"""
飞书认证模块 - 获取和管理 tenant_access_token

Token 有效期 2 小时，自动刷新。
使用 飞书开放平台 的自建应用获取凭证。
"""
import time
from typing import Optional

import httpx
from loguru import logger


class FeishuAuth:
    """飞书 tenant_access_token 管理器"""

    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    def __init__(self, app_id: str, app_secret: str):
        """
        Args:
            app_id: 飞书应用的 App ID
            app_secret: 飞书应用的 App Secret
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self._token: Optional[str] = None
        self._expires_at: float = 0  # 过期时间戳

    async def get_token(self) -> Optional[str]:
        """
        获取有效的 tenant_access_token

        如果缓存中的 token 还在有效期内，直接返回。
        否则重新请求。

        Returns:
            token 字符串，失败返回 None
        """
        # 提前 5 分钟刷新，防止边界过期
        if self._token and time.time() < self._expires_at - 300:
            return self._token

        return await self._refresh_token()

    async def _refresh_token(self) -> Optional[str]:
        """请求新的 tenant_access_token"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.TOKEN_URL,
                    json={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret,
                    },
                )
                data = resp.json()

                if data.get("code") != 0:
                    logger.error(f"飞书认证失败: {data.get('msg', '未知错误')}")
                    return None

                self._token = data["tenant_access_token"]
                self._expires_at = time.time() + data.get("expire", 7200)
                logger.debug("飞书 tenant_access_token 已刷新")
                return self._token

        except httpx.TimeoutException:
            logger.error("飞书认证请求超时")
            return None
        except Exception as e:
            logger.error(f"飞书认证请求失败: {e}")
            return None

    @property
    def is_authenticated(self) -> bool:
        """是否已认证（可能有缓存的 token）"""
        return self._token is not None and time.time() < self._expires_at
