@echo off
title Employee Verification Portal
cd /d "%~dp0backend"
echo ============================================================
echo   Employee Verification Portal
echo   First run: about 5 minutes. Later runs: about 15 seconds.
echo   Keep this window open while you use the app.
echo ============================================================

rem ---------- find Python 3.10 - 3.12 ----------
set "PY="
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12"
if not defined PY py -3.11 -c "import sys" >nul 2>&1 && set "PY=py -3.11"
if not defined PY py -3.10 -c "import sys" >nul 2>&1 && set "PY=py -3.10"
if not defined PY python -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,12) else 1)" >nul 2>&1 && set "PY=python"
if not defined PY goto :fail_python

rem ---------- virtual environment + packages (first run only) ----------
if not exist ".venv\Scripts\python.exe" (
  echo Creating a virtual environment...
  %PY% -m venv .venv
  if errorlevel 1 goto :fail
)
set "VPY=%CD%\.venv\Scripts\python.exe"
if not exist ".venv\installed.ok" (
  echo Installing packages - takes 2-5 minutes the first time...
  "%VPY%" -m pip install --upgrade pip
  "%VPY%" -m pip install -r requirements.txt
  if errorlevel 1 goto :fail
  echo ok> ".venv\installed.ok"
)
if not exist ".env" copy ".env.example" ".env" >nul

rem ---------- SFace model (38 MB, OpenCV model zoo) if it is missing ----------
set "SFACE=app\face\models\face_recognition_sface_2021dec.onnx"
if not exist "%SFACE%" (
  echo Downloading the SFace face model - 38 MB, one time only...
  powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx' -OutFile '%SFACE%'"
  if not exist "%SFACE%" goto :fail
)

rem ---------- start ----------
echo Starting at http://localhost:8000 - sign in with admin / Admin@123
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 120;$i++){try{Invoke-WebRequest 'http://localhost:8000/api/health' -UseBasicParsing -TimeoutSec 2 | Out-Null; Start-Process 'http://localhost:8000'; break}catch{Start-Sleep -Seconds 2}}"
"%VPY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
exit /b 0

:fail_python
echo Python 3.10-3.12 not found. Install Python 3.12 from python.org - tick "Add python.exe to PATH".
pause
exit /b 1
:fail
echo Setup failed - see the messages above.
pause
exit /b 1
