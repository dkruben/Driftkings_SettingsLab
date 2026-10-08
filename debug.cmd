@echo off
call "%~dp0build_tools\run_build.cmd" debug
exit /b %ERRORLEVEL%
