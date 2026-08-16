"""
反检测模块 - 防止被抖音识别为自动化工具

通过注入 JavaScript 脚本覆盖浏览器指纹特征，模拟真实用户环境。
"""
from loguru import logger
from playwright.async_api import BrowserContext


async def apply_stealth_patches(context: BrowserContext):
    """
    应用反检测脚本到浏览器上下文

    覆盖以下指纹特征:
    - navigator.webdriver → undefined (默认是 true)
    - chrome.runtime → 模拟存在
    - navigator.permissions → 伪装通知权限
    - navigator.plugins → 模拟插件列表
    - navigator.languages → 中文本地化
    - WebGL 指纹 → 可选 (暂不实现，够用)
    """
    logger.debug("正在应用反检测脚本...")

    # 1. 隐藏 WebDriver 特征
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
    """)

    # 2. 模拟 Chrome 运行时
    await context.add_init_script("""
        window.chrome = {
            runtime: {
                connect: () => {},
                sendMessage: () => {},
                onMessage: { addListener: () => {} },
                onConnect: { addListener: () => {} },
            },
            loadTimes: () => {},
            csi: () => {},
            app: { isInstalled: false },
        };
    """)

    # 3. 伪装通知权限
    await context.add_init_script("""
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (params) => {
            if (params.name === 'notifications') {
                return Promise.resolve({ state: 'denied' });
            }
            return originalQuery(params);
        };
    """)

    # 4. 模拟浏览器插件数量（正常用户通常有 3-5 个插件）
    await context.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' },
            ],
        });
    """)

    # 5. 设置语言偏好
    await context.add_init_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en'],
        });
    """)

    # 6. 覆盖媒体硬件信息（模拟真实设备）
    await context.add_init_script("""
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });
    """)

    logger.debug("反检测脚本已应用")


async def apply_extra_stealth(page):
    """
    针对单个页面的额外反检测（必须在 page.goto() 之前调用）

    注入 WebGL 指纹覆写等更精细的伪装脚本
    """
    await page.add_init_script("""
        // 覆写 Canvas 指纹
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            if (this.width === 0 || this.height === 0) return originalToDataURL.call(this, type);
            const ctx = this.getContext('2d');
            if (ctx) {
                const noise = 0.5 + Math.random() * 0.5;
                const imageData = ctx.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] = Math.min(255, Math.max(0, imageData.data[i] + noise));
                }
                ctx.putImageData(imageData, 0, 0);
            }
            return originalToDataURL.call(this, type);
        };
    """)
