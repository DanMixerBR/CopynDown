@echo off
title CopynDown Updater
cls

:: ANSI Color Definitions
set "ESC="
set "G=%ESC%[92m"
set "C=%ESC%[96m"
set "W=%ESC%[0m"
set "Y=%ESC%[93m"

echo %C%=======================================================%W%
echo           %G%CopynDown%W% - %Y%Update Manager%W%
echo %C%=======================================================%W%
echo.
echo %C%[%W%*%C%]%W% Status: %Y%Cleaning up legacy files...%W%
del /f /q "YT Video Downloader.bat" "YT Music Downloader.bat" "YT MP3 Converter.bat" "Insta Video Downloader.bat" "Auto Update.bat" >nul 2>&1
del /f /q "Readme (EN).txt" "Readme (PT).txt" "YT.Video.Downloader.zip" >nul 2>&1

echo %C%[%W%*%C%]%W% Status: %Y%Extracting new files...%W%
set "ZIP_FILE="
if exist "CopynDown_Windows.zip" set "ZIP_FILE=CopynDown_Windows.zip"
if exist "CopynDown.zip" set "ZIP_FILE=CopynDown.zip"

if not defined ZIP_FILE exit /b

if exist "certifi" (
    rmdir /s /q "certifi" "charset_normalizer" "cryptography" "customtkinter" "PIL" "tcl" "tcl8" "tk" >nul 2>&1
    del /f /q "_tkinter.pyd" "pyexpat.pyd" "python3.dll" "_asyncio.pyd" "_cffi_backend.pyd" "_multiprocessing.pyd" "_overlapped.pyd" >nul 2>&1
    set "DEST_PATH=.."
) else (
    robocopy "bin" "core\bin" /MOVE /E /IS >nul 2>&1
    set "DEST_PATH=."
)

powershell -command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%DEST_PATH%' -Force"
del /f /q "%ZIP_FILE%"

echo.
echo %G%-------------------------------------------------------%W%
echo   [SUCCESS] Update completed!
echo   Please restart the app.
echo %G%-------------------------------------------------------%W%
echo.

timeout /t 5

:: Self-deletion logic to keep the workspace clean
start /b "" cmd /c "timeout /t 1 >nul & del /f /q "%~f0""
exit
