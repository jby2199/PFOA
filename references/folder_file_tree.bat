@echo off
setlocal enabledelayedexpansion

REM 현재 BAT 파일이 위치한 디렉터리를 기준으로 대상 디렉터리 경로를 설정합니다.
set targetDirectory=%~dp0

tree /f "%targetDirectory%" > "%targetDirectory%\folder_file_tree.txt"

exit /b

endlocal