"""
飞书多维表格客户端 - 管理采集目标列表

从飞书多维表格中读取/写入采集目标。
表格结构:
| 名称 (文本) | 类型 (单选) | 抖音ID (文本) | 状态 (单选) | 备注 (文本) |
"""
from typing import Optional

import httpx
from loguru import logger

from models.schemas import ScrapeTarget, TargetType, TargetStatus
from .auth import FeishuAuth


class BitableClient:
    """飞书多维表格客户端"""

    API_BASE = "https://open.feishu.cn/open-apis/bitable/v1"

    def __init__(self, auth: FeishuAuth, app_token: str, table_id: str):
        self.auth = auth
        self.app_token = app_token
        self.table_id = table_id

    async def add_target(self, name: str, douyin_id: str,
                          target_type: TargetType = TargetType.USER) -> bool:
        """
        添加新的采集目标到多维表格

        Args:
            name: 显示名称
            douyin_id: 抖音 sec_uid（用户）或 hashtag_id
            target_type: 目标类型

        Returns:
            是否成功
        """
        token = await self.auth.get_token()
        if not token:
            logger.error("飞书未认证")
            return False

        url = f"{self.API_BASE}/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {
            "fields": {
                "名称": name,
                "类型": target_type.value,
                "抖音ID": douyin_id,
                "状态": "active",
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=body)
                data = resp.json()

            if data.get("code") == 0:
                record_id = data.get("data", {}).get("record", {}).get("record_id", "")
                logger.info(f"✅ 目标已添加到飞书: {name} ({record_id})")
                return True
            else:
                logger.error(f"添加目标失败: {data.get('msg')}")
                return False

        except Exception as e:
            logger.error(f"添加目标出错: {e}")
            return False

    async def get_targets(self) -> list[ScrapeTarget]:
        """获取所有活跃的采集目标"""
        token = await self.auth.get_token()
        if not token:
            logger.error("飞书未认证，无法读取多维表格")
            return []

        targets = []
        page_token = None

        try:
            while True:
                url = f"{self.API_BASE}/apps/{self.app_token}/tables/{self.table_id}/records"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
                params = {"page_size": 20}
                if page_token:
                    params["page_token"] = page_token

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, headers=headers, params=params)
                    data = resp.json()

                if data.get("code") != 0:
                    logger.error(f"读取多维表格失败: {data.get('msg', '未知错误')}")
                    break

                items = data.get("data", {}).get("items", [])
                for record in items:
                    fields = record.get("fields", {})
                    target = self._parse_record(fields)
                    if target and target.status == TargetStatus.ACTIVE:
                        targets.append(target)

                if not data.get("data", {}).get("has_more"):
                    break
                page_token = data["data"].get("page_token")

            logger.info(f"从多维表格读取到 {len(targets)} 个活跃目标")
            return targets

        except httpx.TimeoutException:
            logger.error("读取飞书多维表格超时")
            return []
        except Exception as e:
            logger.error(f"读取飞书多维表格失败: {e}")
            return []

    def _parse_record(self, fields: dict) -> Optional[ScrapeTarget]:
        """解析飞书表格中的一条记录"""
        try:
            name = fields.get("名称", "")
            if not name:
                return None

            type_field = fields.get("类型", "")
            if isinstance(type_field, dict):
                type_value = type_field.get("text", "")
            else:
                type_value = str(type_field) if type_field else ""

            target_type = TargetType.USER if type_value == "user" else TargetType.HASHTAG

            douyin_id = fields.get("抖音ID", "")
            if not douyin_id:
                logger.warning(f"目标 '{name}' 缺少抖音ID，跳过")
                return None

            status_field = fields.get("状态", "active")
            if isinstance(status_field, dict):
                status_value = status_field.get("text", "active")
            else:
                status_value = str(status_field) if status_field else "active"

            status = TargetStatus.ACTIVE if status_value == "active" else TargetStatus.PAUSED
            notes = fields.get("备注", "") or ""

            return ScrapeTarget(
                name=name,
                target_type=target_type,
                douyin_id=douyin_id.strip(),
                status=status,
                notes=notes,
            )

        except Exception as e:
            logger.warning(f"解析多维表格记录失败: {e}")
            return None
