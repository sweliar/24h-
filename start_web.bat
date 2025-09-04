@echo off

REM 检查是否已安装Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 安装依赖
pip install -r requirements.txt

REM 启动Web服务器
echo 正在启动会议录音助手Web界面...
echo 请在浏览器中访问 http://localhost:5000
echo 按Ctrl+C可停止服务器
python app.py