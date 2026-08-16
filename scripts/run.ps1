<#
.SYNOPSIS
手动运行抖音文案采集

.DESCRIPTION
激活虚拟环境后执行一次完整采集

.USAGE
.\scripts\run.ps1              # 正常采集
.\scripts\run.ps1 -DryRun      # 试运行（不写飞书）
.\scripts\run.ps1 -NoTranscribe  # 跳过语音转文字
.\scripts\run.ps1 -ShowBrowser  # 显示浏览器界面（调试）
.\scripts\run.ps1 -Login        # 抖音扫码登录
#>

param(
    [switch]$DryRun,
    [switch]$NoTranscribe,
    [switch]$ShowBrowser,
    [switch]$Login
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ProjectRoot

# 激活虚拟环境
$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "❌ 未找到虚拟环境，请先运行 scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

# 构建命令
$argsList = @($venvPython, "main.py")

if ($Login) {
    $argsList += @("--mode", "login", "--no-headless")
} else {
    $argsList += @("--mode", "once")
    if ($DryRun) { $argsList += "--dry-run" }
    if ($NoTranscribe) { $argsList += "--no-transcribe" }
    if ($ShowBrowser) { $argsList += "--no-headless" }
}

Write-Host "🚀 运行: $($argsList -join ' ')" -ForegroundColor Cyan
Write-Host ""

# 执行
& $argsList[0] $argsList[1..($argsList.Length-1)]

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 执行完成" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 执行失败 (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}
