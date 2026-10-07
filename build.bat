@echo off
rem Windows entry point for tools\build\build.sh (needs Git for Windows, Python 3, xdelta3; see docs\GETTING_STARTED.md).
rem Usage: build.bat "C:\path\to\KimiKiss dump.iso" [output.iso]
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: build.bat "C:\path\to\KimiKiss dump.iso" [output.iso]
  exit /b 2
)
set "GITBASH="
for %%P in ("%ProgramFiles%\Git\bin\bash.exe" "%ProgramFiles(x86)%\Git\bin\bash.exe" "%LocalAppData%\Programs\Git\bin\bash.exe") do (
  if exist %%P set "GITBASH=%%~P"
)
if not defined GITBASH (
  echo Git for Windows was not found. Install it from https://git-scm.com/download/win and run this again.
  exit /b 1
)
set "OUT=%~2"
if "%OUT%"=="" set "OUT=build/KimiKiss_EN.iso"
"%GITBASH%" tools/build/build.sh "%~1" "%OUT%"
exit /b %ERRORLEVEL%
