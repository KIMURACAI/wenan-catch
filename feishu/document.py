"""
飞书文档客户端 - 管理抖音文案账号文档

每个目标账号对应一个飞书文档。
文档名称 = 账号名称。
"""
from typing import Optional

import httpx
from loguru import logger

from .auth import FeishuAuth


class DocumentClient:
    """飞书文档客户端"""

    DOCX_API_BASE = "https://open.feishu.cn/open-apis/docx/v1"
    DRIVE_API_BASE = "https://open.feishu.cn/open-apis/drive/v1"

    def __init__(self, auth: FeishuAuth, folder_token: Optional[str] = None):
        self.auth = auth
        self.folder_token = folder_token

    async def ensure_account_document(
        self, account_name: str
    ) -> tuple[Optional[str], Optional[str]]:
        """
        确保账号文档存在

        按标题搜索，不存在则创建。

        Args:
            account_name: 账号名称（如"奇门小道"）

        Returns:
            (doc_token, doc_url) 或 (None, None)
        """
        # 先搜索现有文档
        doc_token, doc_url = await self._find_document_by_title(account_name)
        if doc_token:
            logger.info(f"找到账号文档: {account_name}")
            return doc_token, doc_url

        # 不存在则创建
        logger.info(f"创建账号文档: {account_name}")
        return await self._create_document(account_name)

    async def _find_document_by_title(
        self, title: str
    ) -> tuple[Optional[str], Optional[str]]:
        """按标题搜索文档"""
        token = await self.auth.get_token()
        if not token:
            return None, None

        headers = {"Authorization": f"Bearer {token}"}

        try:
            if self.folder_token:
                url = f"{self.DRIVE_API_BASE}/files"
                params = {"page_size": 50, "folder_token": self.folder_token}

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, headers=headers, params=params)
                    data = resp.json()

                if data.get("code") == 0:
                    files = data.get("data", {}).get("files", [])
                    for f in files:
                        if f.get("name") == title and f.get("type") == "docx":
                            return f.get("token"), f.get("url")

            return None, None
        except Exception as e:
            logger.debug(f"搜索文档失败: {e}")
            return None, None

    async def _create_document(
        self, title: str
    ) -> tuple[Optional[str], Optional[str]]:
        """创建新文档"""
        token = await self.auth.get_token()
        if not token:
            return None, None

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.DOCX_API_BASE}/documents",
                    headers=headers,
                    json={"title": title},
                )
                data = resp.json()

            if data.get("code") != 0:
                logger.error(f"创建文档失败: {data.get('msg')}")
                return None, None

            doc_token = data["data"]["document"]["document_id"]
            doc_url = f"https://bytedance.feishu.cn/docx/{doc_token}"
            logger.info(f"文档已创建: {doc_url}")

            # 移到指定文件夹
            if self.folder_token:
                await self._move_to_folder(doc_token, self.folder_token, token)

            return doc_token, doc_url

        except httpx.TimeoutException:
            logger.error("创建文档超时")
            return None, None
        except Exception as e:
            logger.error(f"创建文档失败: {e}")
            return None, None

    async def _move_to_folder(self, doc_token: str, folder_token: str, token: str):
        """将文档移到目标文件夹"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.DRIVE_API_BASE}/files/{doc_token}/move",
                    headers=headers,
                    json={"type": "docx", "folder_token": folder_token},
                )
                data = resp.json()
                if data.get("code") == 0:
                    logger.info(f"文档已移到目标文件夹")
                else:
                    logger.warning(
                        f"移动文档到文件夹失败: {data.get('msg')}。\n"
                        f"请将应用添加为文件夹协作者。"
                    )
        except Exception as e:
            logger.debug(f"移动文档失败: {e}")

    async def append_content(
        self, doc_token: str, blocks: list[dict]
    ) -> bool:
        """向文档末尾追加内容块"""
        token = await self.auth.get_token()
        if not token:
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            root_block_id = doc_token
            batch_size = 50

            for i in range(0, len(blocks), batch_size):
                batch = blocks[i : i + batch_size]
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        f"{self.DOCX_API_BASE}/documents/{doc_token}/blocks/{root_block_id}/children",
                        headers=headers,
                        json={"children": batch, "index": -1},
                    )
                    data = resp.json()

                if data.get("code") != 0:
                    logger.error(f"追加内容失败: {data.get('msg')}")
                    return False

            logger.info(f"内容追加完成，共 {len(blocks)} 个块")
            return True

        except httpx.TimeoutException:
            logger.error("追加内容超时")
            return False
        except Exception as e:
            logger.error(f"追加内容失败: {e}")
            return False
