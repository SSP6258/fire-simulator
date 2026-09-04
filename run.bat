@echo off
chcp 65001 >nul
setlocal

rem ---------------------------------------------------------------
rem  FIRE 財務自由模擬器 —— 本機啟動用
rem
rem  用法：
rem    直接雙擊，或在終端機下 run.bat
rem    run.bat 8502     ← 指定其他 port（預設 8501）
rem ---------------------------------------------------------------

rem 切到這支 .bat 所在的目錄，這樣從任何地方雙擊都不會跑錯位置
cd /d "%~dp0"

set "PORT=%~1"
if "%PORT%"=="" set "PORT=8501"

set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo.
    echo [錯誤] 找不到虛擬環境：%CD%\.venv
    echo.
    echo 請先建立環境：
    echo     py -3.13 -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    echo.
    goto :halt
)

rem 用 python -m streamlit 而不是 streamlit.exe。
rem 原因：venv 的 .exe 啟動器把絕對路徑寫死在檔案裡，專案資料夾一搬就全部失效，
rem 而 python.exe 是靠自己的位置解析 sys.prefix，搬到哪都能用。
rem 這支 .bat 因此對「專案被搬走」免疫。

rem 主控台預設 cp950 吃不下 emoji 與部分中文，會噴 UnicodeEncodeError
set "PYTHONIOENCODING=utf-8"

echo.
echo   FIRE 財務自由模擬器
echo   http://localhost:%PORT%
echo.
echo   按 Ctrl+C 結束
echo.

"%VENV_PY%" -m streamlit run streamlit_app.py --server.port %PORT%

if errorlevel 1 (
    echo.
    echo [錯誤] Streamlit 異常結束 ^(exit code %errorlevel%^)
    echo 若訊息是 port 已被占用，換一個：run.bat 8502
    goto :halt
)

goto :eof

:halt
echo 按任意鍵關閉視窗...
pause >nul
endlocal
exit /b 1
