<#
.SYNOPSIS
注册 Windows 定时任务，每天自动执行抖音文案采集

.DESCRIPTION
使用 Windows Task Scheduler 注册每日定时任务。
默认每天 08:00 执行一次采集。
可以在 .env 文件中修改 DAILY_RUN_TIME 来调整执行时间。

.USAGE
.\scripts\register_task.ps1              # 注册定时任务
.\scripts\register_task.ps1 -Unregister  # 删除定时任务
.\scripts\register_task.ps1 -Time 09:30  # 指定执行时间
#>

param(
    [switch]$Unregister,
    [string]$Time = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ProjectRoot

$TaskName = "DouyinWenanCatch"

if ($Unregister) {
    Write-Host "🗑️  删除定时任务: $TaskName" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ 已删除" -ForegroundColor Green
    exit 0
}

# 确定执行时间
if (-not $Time) {
    # 尝试从 .env 读取
    $envFile = Join-Path $ProjectRoot ".env"
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile -Raw
        if ($envContent -match 'DAILY_RUN_TIME=(\d{2}:\d{2})') {
            $Time = $Matches[1]
        }
    }
}
if (-not $Time) {
    $Time = "08:00"  # 默认 8 点
}

$hour, $minute = $Time -split ":"
Write-Host "⏰ 采集时间: 每天 $Time" -ForegroundColor Cyan

# Python 执行路径
$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    # 尝试系统 Python
    $venvPython = "python"
}

$ActionArgs = "main.py --mode once"

# 创建定时任务
$Action = New-ScheduledTaskAction `
    -Execute $venvPython `
    -Argument $ActionArgs `
    -WorkingDirectory $ProjectRoot

$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 10)

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Limited

Write-Host "📝 正在注册定时任务: $TaskName" -ForegroundColor Yellow

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Force

    Write-Host ""
    Write-Host "✅ 定时任务注册成功！" -ForegroundColor Green
    Write-Host "   任务名称: $TaskName" -ForegroundColor White
    Write-Host "   执行时间: 每天 $Time" -ForegroundColor White
    Write-Host "   执行程序: $venvPython" -ForegroundColor White
    Write-Host ""
    Write-Host "📌 管理定时任务:" -ForegroundColor Cyan
    Write-Host "   查看任务: taskschd.msc (任务计划程序)" -ForegroundColor White
    Write-Host "   删除任务: .\scripts\register_task.ps1 -Unregister" -ForegroundColor White

} catch {
    Write-Host "❌ 注册失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 提示: 请以管理员身份运行 PowerShell" -ForegroundColor Yellow
    exit 1
}
