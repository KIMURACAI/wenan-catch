"""
添加抖音目标到飞书多维表格

用法:
  python add_target.py <抖音主页URL> <名称>

示例:
  python add_target.py https://www.douyin.com/user/MS4wLjABAAAA... 奇门小道
"""
import sys
import re
import asyncio
from urllib.parse import urlparse, parse_qs

import httpx
from loguru import logger

sys.path.insert(0, ".")

from config import settings
from feishu.auth import FeishuAuth
from feishu.bitable import BitableClient
from models.schemas import TargetType


def extract_sec_uid(url: str) -> str:
    """从抖音主页URL提取 sec_uid"""
    # 标准格式: https://www.douyin.com/user/MS4wLjABAAAA...
    m = re.search(r'/user/([^/?&]+)', url)
    if m:
        return m.group(1)

    # 短链接格式: https://v.douyin.com/xxxx/
    m = re.search(r'v\.douyin\.com/(\w+)', url)
    if m:
        return f"short:{m.group(1)}"  # 标记为短链接，需要解析

    raise ValueError(f"无法从URL提取sec_uid: {url}")


async def resolve_short_url(url: str) -> str:
    """解析抖音短链接，获取真实URL"""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url)
            final_url = str(resp.url)
            if "/user/" in final_url:
                return final_url
            return url
    except Exception as e:
        logger.warning(f"短链接解析失败: {e}")
        return url


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    name = sys.argv[2]

    # 解析短链接
    if "v.douyin.com" in url:
        logger.info("检测到短链接，正在解析...")
        url = await resolve_short_url(url)

    # 提取 sec_uid
    try:
        sec_uid = extract_sec_uid(url)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"名称: {name}")
    logger.info(f"抖音ID (sec_uid): {sec_uid[:20]}...")

    # 写入飞书
    auth = FeishuAuth(settings.feishu_app_id, settings.feishu_app_secret)
    bitable = BitableClient(
        auth,
        settings.feishu_bitable_app_token,
        settings.feishu_target_table_id,
    )

    success = await bitable.add_target(
        name=name,
        douyin_id=sec_uid,
        target_type=TargetType.USER,
    )

    if success:
        print(f"\n✅ {name} 已添加到飞书！下次运行采集即可生效。")
    else:
        print(f"\n❌ 添加失败，详情见日志")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
