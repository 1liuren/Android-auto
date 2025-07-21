@echo off
chcp 65001 > nul
echo ================================
echo   📦 PyInstaller 代码打包工具
echo ================================
echo.

echo 🔧 正在检查PyInstaller安装状态...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ❌ PyInstaller 未安装，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ PyInstaller 安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo ✅ PyInstaller 安装成功！
) else (
    echo ✅ PyInstaller 已安装
)

echo.
echo 🚀 开始打包程序...
echo.

REM 创建打包命令
pyinstaller ^
    --onefile ^
    --windowed ^
    --name="phone-agent工具" ^
    --add-data="app;app" ^
    --add-data="src;src" ^
    --add-data="utils;utils" ^
    --add-data="requirements.txt;." ^
    --collect-data="uiautomator2" ^
    --exclude-module="matplotlib" ^
    --exclude-module="PIL.ImageQt" ^
    --exclude-module="IPython" ^
    --exclude-module="jupyter" ^
    --exclude-module="notebook" ^
    --exclude-module="pytest" ^
    --exclude-module="pkg_resources" ^
    --exclude-module="wheel" ^
    --exclude-module="pip" ^
    --exclude-module="torch" ^
    --exclude-module="torchvision" ^
    --exclude-module="torchaudio" ^
    --exclude-module="sympy" ^
    --exclude-module="pyarrow" ^
    --exclude-module="botocore" ^
    --exclude-module="boto3" ^
    --exclude-module="tensorboard" ^
    --hidden-import="tkinter" ^
    --hidden-import="tkinter.ttk" ^
    --hidden-import="tkinter.filedialog" ^
    --hidden-import="tkinter.messagebox" ^
    --hidden-import="threading" ^
    --hidden-import="queue" ^
    --hidden-import="numpy" ^
    --hidden-import="pandas" ^
    --hidden-import="openpyxl" ^
    --hidden-import="requests" ^
    --hidden-import="uiautomator2" ^
    --hidden-import="uiautomator2.exceptions" ^
    --hidden-import="uiautomator2.session" ^
    --hidden-import="ttkthemes" ^
    --hidden-import="src.gui_config" ^
    --hidden-import="loguru" ^
    --hidden-import="adbutils" ^
    --hidden-import="cv2" ^
    --hidden-import="lxml" ^
    --hidden-import="lxml.etree" ^
    --hidden-import="lxml.html" ^
    --hidden-import="PIL" ^
    --hidden-import="PIL.Image" ^
    --hidden-import="dashscope" ^
    --hidden-import="scipy" ^
    --hidden-import="scipy.stats" ^
    --hidden-import="jaraco" ^
    --hidden-import="jaraco.text" ^
    gui_app_new.py

if errorlevel 1 (
    echo.
    echo ❌ 打包失败！请检查错误信息
    pause
    exit /b 1
)

echo.
echo 🎉 打包成功！
echo.
echo 📁 生成的文件位置：
echo    dist\phone-agent工具.exe
echo.
echo 📊 文件信息：
if exist "dist\phone-agent工具.exe" (
    for %%I in ("dist\phone-agent工具.exe") do echo    文件大小: %%~zI 字节 ^(~%%~zI/1024/1024 MB^)
)

echo.
echo 💡 使用说明：
echo    1. 可以直接运行 dist\phone-agent工具.exe
echo    2. 该文件包含所有依赖，无需Python环境
echo    3. 可以复制到其他Windows电脑运行
echo.

set /p choice="是否要打开输出目录？(y/n): "
if /i "%choice%"=="y" (
    explorer dist
)

echo.
echo 🎊 操作完成！
pause