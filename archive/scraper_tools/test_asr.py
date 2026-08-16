"""
快速ASR测试 - 用数据库里已有的视频地址直接测
"""
import asyncio, subprocess, json, time, httpx, uuid, re, sqlite3
from pathlib import Path

API_KEY = "9f71db70-283d-4a26-840b-d30668fd04d9"
FFMPEG = r"C:\Users\Kimura\AppData\Local\ffmpegio\ffmpeg-downloader\ffmpeg\bin\ffmpeg.exe"
TEMP = Path("data/test_asr")
TEMP.mkdir(parents=True, exist_ok=True)


async def test_one_video(video_url, post_id):
    """测试单条视频的完整链路"""
    mp4 = TEMP / f"{post_id}.mp4"
    wav = TEMP / f"{post_id}.wav"

    print(f"\n{'='*60}")
    print(f"测试视频: {post_id}")
    print(f"{'='*60}")

    # 1. 下载
    print(f"\n[1/4] 下载视频...")
    t0 = time.time()
    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        resp = await client.get(video_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0",
            "Referer": "https://www.douyin.com/",
        })
        mp4.write_bytes(resp.content)
    size_mb = mp4.stat().st_size / 1024 / 1024
    print(f"  大小: {size_mb:.1f} MB, 耗时: {time.time()-t0:.0f}秒")

    # 2. 查视频信息
    r = subprocess.run([FFMPEG.replace("ffmpeg.exe", "ffprobe.exe"),
                       "-v", "quiet", "-print_format", "json",
                       "-show_format", str(mp4)],
                      capture_output=True, text=True)
    info = json.loads(r.stdout)
    dur = float(info["format"]["duration"])
    print(f"  视频时长: {dur:.1f} 秒")

    # 3. 提取音频
    print(f"\n[2/4] 提取音频...")
    t0 = time.time()
    subprocess.run([FFMPEG, "-i", str(mp4), "-vn",
                   "-acodec", "pcm_s16le", "-ar", "16000",
                   "-ac", "1", "-y", str(wav)],
                  capture_output=True)
    wav_mb = wav.stat().st_size / 1024 / 1024
    dur_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)",
        subprocess.run([FFMPEG, "-i", str(wav)], capture_output=True, text=True).stderr)
    if dur_match:
        h, m, s = dur_match.groups()
        audio_dur = int(h)*3600 + int(m)*60 + float(s)
        print(f"  音频时长: {audio_dur:.1f} 秒, 大小: {wav_mb:.2f} MB")

    # 4. 上传
    print(f"\n[3/4] 上传音频...")
    t0 = time.time()
    async with httpx.AsyncClient(timeout=30) as client:
        with open(wav, "rb") as f:
            resp = await client.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                data={"reqtype": "fileupload", "time": "1h"},
                files={"fileToUpload": (wav.name, f, "audio/wav")},
            )
            audio_url = resp.text.strip()
    print(f"  上传完成: {time.time()-t0:.0f}秒")

    # 5. ASR
    print(f"\n[4/4] 火山引擎 ASR...")
    t0 = time.time()
    task_id = str(uuid.uuid4())
    body = json.dumps({
        "user": {"uid": "test"},
        "audio": {
            "url": audio_url, "format": "wav", "codec": "raw",
            "rate": 16000, "bits": 16, "channel": 1,
        },
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True, "enable_punc": True,
        }
    })
    headers = {
        "x-api-key": API_KEY, "X-Api-Resource-Id": "volc.bigasr.auc",
        "X-Api-Request-Id": task_id, "X-Api-Sequence": "-1",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit",
            data=body, headers=headers,
        )
        code = resp.headers.get("X-Api-Status-Code", "")
        if code != "20000000":
            print(f"  提交失败: {resp.headers.get('X-Api-Message', code)}")
            return
        print(f"  任务已提交...")

    for attempt in range(60):
        await asyncio.sleep(3)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query",
                data=json.dumps({}), headers=headers,
            )
            code = resp.headers.get("X-Api-Status-Code", "")
            if code == "20000000":
                result = resp.json()
                text = result.get("result", {}).get("text", "") or ""
                elapsed = time.time() - t0
                print(f"\n{'='*60}")
                print(f"ASR 结果: {len(text)} 字 (耗时 {elapsed:.0f}秒)")
                print(f"{'='*60}")
                print(text if text else "(空)")
                if text and len(text) < 30 and dur > 10:
                    print(f"\n⚠️  视频 {dur:.0f}秒, 只识别出 {len(text)} 字")
                return text
            elif code == "20000003":
                print(f"\n→ 静音音频 (视频{dur:.0f}秒)")
                return ""
            elif code in ("20000001", "20000002"):
                continue
            else:
                print(f"\n→ 查询失败: code={code}")
                return ""
    print(f"\n→ 超时")


async def main():
    # 从数据库拿一条 pending 的视频
    conn = sqlite3.connect(r"E:\wenan catch\data\wenan_catch.db")
    row = conn.execute(
        "SELECT post_id, video_url FROM posts WHERE transcribe_status='pending' LIMIT 1"
    ).fetchone()
    conn.close()

    if not row:
        print("数据库没有待处理的视频")
        return

    post_id, video_url = row
    print(f"从数据库取到视频: {post_id}")

    result = await test_one_video(video_url, post_id)

    if result:
        print(f"\n✅ 识别成功!")
    else:
        print(f"\n❌ 识别失败")

    # 清理
    for f in TEMP.glob("*"):
        f.unlink()
    TEMP.rmdir()


if __name__ == "__main__":
    asyncio.run(main())
