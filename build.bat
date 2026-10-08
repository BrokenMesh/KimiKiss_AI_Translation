@echo off
rem Windows entry point for tools\build\build.sh (needs Git for Windows, Python 3, xdelta3; see docs\GETTING_STARTED.md).
rem Usage: build.bat "C:\path\to\KimiKiss dump.iso" [output.iso] [--no-xdelta]
rem Output: build\KimiKiss_EN.iso and build\KimiKiss_EN.iso.xdelta (a bare output name goes into build\).
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: build.bat "C:\path\to\KimiKiss dump.iso" [output.iso] [--no-xdelta]
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
"%GITBASH%" tools/build/build.sh %*
exit /b %ERRORLEVEL%
