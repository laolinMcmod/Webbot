@echo off
chcp 65001 >nul
rem ============================================================
rem  网页爬虫工具 双击启动脚本
rem  自动进入本脚本所在目录，激活虚拟环境后运行 main.py
rem ============================================================
cd /d "%~dp0"
title 网页爬虫工具（遵守 robots.txt · 内置浏览器预览）

".venv\Scripts\python.exe" main.py

rem  如果程序出错退出，保留窗口显示错误信息，方便排查
if errorlevel 1 (
    echo.
    echo 程序异常退出，请把上面的错误信息发给助手查看。
    pause >nul
)
