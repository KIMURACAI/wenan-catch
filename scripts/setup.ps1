<#
.SYNOPSIS
抖音文案采集系统 - 一键安装脚本

.DESCRIPTION
创建虚拟环境、安装 Python 依赖、安装 Playwright 浏览器、复制 .env 配置模板

.USAGE
.\scripts\setup.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  抖音文案采集系统 - 安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Python
Write-Host "[1/5] 检查 Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Python: $pythonVersion"

# 2. 创建虚拟环境
Write-Host "[2/5] 创建虚拟环境..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ 虚拟环境已创建"
} else {
    Write-Host "⏭️  虚拟环境已存在，跳过"
}

# 激活虚拟环境
$activateScript = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
. $activateScript
Write-Host "✅ 虚拟环境已激活"

# 3. 安装依赖
Write-Host "[3/5] 安装 Python 依赖..." -ForegroundColor Yellow
python -m pip install --upgrade pip -q
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 依赖安装完成"
} else {
    Write-Host "❌ 依赖安装失败" -ForegroundColor Red
    exit 1
}

# 4. 安装 Playwright 浏览器
Write-Host "[4/5] 安装 Playwright Chromium 浏览器..." -ForegroundColor Yellow
playwright install chromium
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Playwright Chromium 安装完成"
} else {
    Write-Host "❌ Playwright 安装失败" -ForegroundColor Red
    exit 1
}

# 5. 配置 .env
Write-Host "[5/5] 配置环境变量..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.template" ".env"
    Write-Host "✅ .env 文件已创建（请在 .env 中填写飞书应用凭证）"
    Write-Host "⚠️  重要：请编辑 .env 文件，填入你的飞书 App ID 和 App Secret"
} else {
    Write-Host "⏭️  .env 文件已存在，跳过"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  🎉 安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Cyan
Write-Host "  1. 编辑 .env 文件，填入飞书应用凭证" -ForegroundColor White
Write-Host "  2. 运行登录: python main.py --mode login" -ForegroundColor White
Write-Host "  3. 测试采集: python main.py --mode once" -ForegroundColor White
Write-Host "  4. 查看帮助: python main.py --help" -ForegroundColor White
Write-Host ""
