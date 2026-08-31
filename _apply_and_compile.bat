@echo off
setlocal
set PY=C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe
set DST=C:\Users\skps9\AppData\Local\hermes\scripts\activity_monitor.py
set SRC=%~dp0_staging\activity_monitor.py

copy /Y "%SRC%" "%DST%" || exit /b 1
echo OK: copied patched activity_monitor.py

for %%F in (
  "C:\Users\skps9\Documents\Code_Project\jarvis-pc\scripts\jarvis_self_monitor.py"
  "C:\Users\skps9\Documents\Code_Project\jarvis-pc\src\jarvis\shell_app.py"
  "C:\Users\skps9\AppData\Local\hermes\scripts\activity_monitor.py"
) do (
  echo === %%~F ===
  "%PY%" -m py_compile "%%~F"
  echo exit_code=!ERRORLEVEL!
)
