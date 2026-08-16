@echo off
chcp 65001 >nul
cd /d "E:\wenan catch"
echo.
echo ========== 扒取指定用户 ==========
echo 输入已在飞书表格中的用户名
echo.
set /p name=用户名:
echo.
echo 开始扒取 %name% 的最新视频...
echo.
python backfill.py "%name%"
echo.
pause
