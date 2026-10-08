@echo off
call "%~dp0build_tools\run_build.cmd" release
exit /b %ERRORLEVEL%
