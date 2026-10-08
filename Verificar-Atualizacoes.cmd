@echo off
py -3 "%~dp0build_tools\check_tool_updates.py" %*
set "update_check_exit=%ERRORLEVEL%"
if not "%~1"=="" exit /b %update_check_exit%
echo.
pause
exit /b %update_check_exit%
