"""
火山引擎录音文件识别（豆包同款引擎） - V3 BigModel API

API 文档: https://www.volcengine.com/docs/6561/1354868

免费额度: 每月 200 万字符，每天 2-4 条视频绰绰有余。

用法:
  1. 在火山引擎控制台开通「语音识别」服务
  2. 在「访问控制」创建 AccessKey
  3. 在 .env 中配置 VOLC_ACCESS_KEY 和 VOLC_APP_ID
  4. config.yaml 设置 transcriber.engine = "volcengine"
"""
import json
import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from config import settings

# V3 API 地址（新版大模型录音文件识别）
VOLC_API = "https://openspeech.bytedance.com/api/v3/auc/bigmodel"


async def _upload_to_catbox(audio_path: Path, timeout: int = 30) -> str:
    """上传音频到 catbox.moe (免费，无需注册，文件无过期时间)"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            with open(audio_path, "rb") as f:
                # catbox 直接用 multipart 上传
                resp = await client.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": (audio_path.name, f, "audio/wav")},
                )
                text = resp.text.strip()
                if text.startswith("https://"):
                    logger.info(f"音频已上传到 catbox: {text}")
                    return text
                logger.warning(f"catbox 上传失败: {text}")
    except Exception as e:
        logger.debug(f"catbox 上传失败: {e}")
    return ""


async def _upload_to_litterbox(audio_path: Path, timeout: int = 30) -> str:
    """上传音频到 litterbox.catbox.moe (1小时后自动删除)"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            with open(audio_path, "rb") as f:
                resp = await client.post(
                    "https://litterbox.catbox.moe/resources/internals/api.php",
                    data={"reqtype": "fileupload", "time": "1h"},
                    files={"fileToUpload": (audio_path.name, f, "audio/wav")},
                )
                text = resp.text.strip()
                if text.startswith("https://"):
                    logger.info(f"音频已上传到 litterbox: {text}")
                    return text
                logger.warning(f"litterbox 上传失败: {text}")
    except Exception as e:
        logger.debug(f"litterbox 上传失败: {e}")
    return ""


async def _upload_from_tmpfiles(audio_path: Path, timeout: int = 30) -> str:
    """备用: 用 tmpfiles.org"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            with open(audio_path, "rb") as f:
                resp = await client.post(
                    "https://tmpfiles.org/api/v1/upload",
                    files={"file": (audio_path.name, f, "audio/wav")},
                )
                data = resp.json()
                if data.get("status") == "success":
                    url = data["data"]["url"]
                    logger.info(f"音频已上传到 tmpfiles: {url}")
                    return url
    except Exception:
        pass
    return ""


async def _upload_audio(audio_path: Path) -> str:
    """
    上传音频到临时文件服务，返回可公开访问的 URL

    依次尝试: catbox → litterbox → tmpfiles
    全部失败后自动重试一轮
    """
    uploaders = [_upload_to_catbox, _upload_to_litterbox, _upload_from_tmpfiles]

    for attempt in range(2):  # 两轮重试
        for uploader in uploaders:
            url = await uploader(audio_path)
            if url:
                return url
            logger.debug(f"{uploader.__name__} 失败，尝试下一个...")
        if attempt == 0:
            logger.info("第一轮上传全部失败，等待5秒后重试...")
            await asyncio.sleep(5)

    logger.error("所有文件上传服务都失败了（两轮重试均失败）")
    return ""


async def transcribe_audio(
    audio_path: Path,
    language: str = "zh",
    timeout: int = 300,
) -> dict:
    """
    使用火山引擎 V3 BigModel ASR 转写音频

    Args:
        audio_path: 音频文件路径
        language: 语言
        timeout: 超时时间（秒）

    Returns:
        {"text": "转写结果", "confidence": None, "error": 错误信息}
    """
    api_key = getattr(settings, 'volc_app_key', '') or os.environ.get('VOLC_APP_KEY', '')

    if not api_key:
        logger.warning(
            "火山引擎未配置！跳过所有转录。\n"
            "请在 .env 中设置:\n"
            "  VOLC_APP_KEY=***\n"
        )
        return {"text": "", "confidence": None, "error": "未配置密钥"}

    if not audio_path.exists():
        return {"text": "", "confidence": None, "error": "音频文件不存在"}

    try:
        # 1. 上传音频到临时 URL
        logger.info("正在上传音频到临时文件服务器...")
        audio_url = await _upload_audio(audio_path)
        if not audio_url:
            return {"text": "", "confidence": None, "error": "音频上传失败"}

        # 2. 提交识别任务
        task_id = str(uuid.uuid4())
        headers = {
            "x-api-key": api_key,
            "X-Api-Resource-Id": "volc.bigasr.auc",
            "X-Api-Request-Id": task_id,
            "X-Api-Sequence": "-1",
            "Content-Type": "application/json",
        }

        request_body = {
            "user": {
                "uid": "wenancatch"
            },
            "audio": {
                "url": audio_url,
                "format": "wav",
                "codec": "raw",
                "rate": 16000,
                "bits": 16,
                "channel": 1,
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "enable_ddc": False,
                "enable_channel_split": False,
                "enable_speaker_info": False,
                "show_utterances": False,
                "vad_segment": False,
                "sensitive_words_filter": "",
            }
        }

        logger.info("正在提交 ASR 任务...")
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{VOLC_API}/submit",
                data=json.dumps(request_body),
                headers=headers,
            )
            status_code = resp.headers.get("X-Api-Status-Code", "")
            x_tt_logid = resp.headers.get("X-Tt-Logid", "")

        if status_code != "20000000":
            msg = resp.headers.get("X-Api-Message", f"提交失败 (code={status_code})")
            logger.error(f"ASR 提交失败: {msg}")
            return {"text": "", "confidence": None, "error": msg}

        logger.info(f"ASR 任务已提交: {task_id}")

        # 3. 轮询识别结果
        for attempt in range(60):
            await asyncio.sleep(3)

            query_headers = {
                "x-api-key": api_key,
                "X-Api-Resource-Id": "volc.bigasr.auc",
                "X-Api-Request-Id": task_id,
                "X-Api-Sequence": "-1",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{VOLC_API}/query",
                    data=json.dumps({}),
                    headers=query_headers,
                )
                code = resp.headers.get("X-Api-Status-Code", "")

            if code == "20000000":
                # 识别完成
                result = resp.json()
                text = result.get("result", {}).get("text", "") or ""
                logger.info(f"ASR 完成: {len(text)} 字")
                return {"text": text.strip(), "confidence": None, "error": None}
            elif code == "20000001":
                # 排队中
                if attempt % 5 == 0:
                    logger.debug(f"ASR 排队中... ({attempt+1}/60)")
                continue
            elif code == "20000002":
                # 处理中
                if attempt % 5 == 0:
                    logger.debug(f"ASR 处理中... ({attempt+1}/60)")
                continue
            elif code == "20000003":
                # 静音音频
                logger.warning(f"静音音频，无识别结果")
                return {"text": "", "confidence": None, "error": "静音音频"}
            else:
                msg = resp.headers.get("X-Api-Message", f"状态码 {code}")
                logger.warning(f"ASR 查询失败: {msg}")
                return {"text": "", "confidence": None, "error": msg}

        logger.warning(f"ASR 超时: {task_id}")
        return {"text": "", "confidence": None, "error": "识别超时"}

    except httpx.TimeoutException:
        logger.error("ASR 请求超时")
        return {"text": "", "confidence": None, "error": "请求超时"}
    except json.JSONDecodeError as e:
        # 捕获 JSON 解析错误，打印原始响应
        logger.error(f"ASR JSON 解析失败: {e}")
        return {"text": "", "confidence": None, "error": f"JSON解析错误: {e}"}
    except httpx.HTTPStatusError as e:
        logger.error(f"ASR HTTP 错误: {e.response.status_code} {e.response.text[:200]}")
        return {"text": "", "confidence": None, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"ASR 未知错误: {type(e).__name__}: {e}")
        return {"text": "", "confidence": None, "error": f"{type(e).__name__}: {e}"}
