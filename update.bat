@echo off
setlocal EnableExtensions EnableDelayedExpansion
title CopynDown Updater
cd /d "%~dp0"
cls

:: ANSI Color Definitions
set "ESC="
set "G=%ESC%[92m"
set "C=%ESC%[96m"
set "W=%ESC%[0m"
set "Y=%ESC%[93m"

set "APP_PID=%~1"
set "MAX_WAIT=60"
set "WAIT_COUNT=0"

echo %C%=======================================================%W%
echo           %G%CopynDown%W% - %Y%Update Manager%W%
echo %C%=======================================================%W%
echo.

if defined APP_PID (
    echo %C%[%W%*%C%]%W% Status: %Y%Waiting for CopynDown to close...%W%

    :wait_app
    tasklist /FI "PID eq %APP_PID%" 2>nul | find "%APP_PID%" >nul
    if not errorlevel 1 (
        set /a WAIT_COUNT+=1

        if !WAIT_COUNT! GEQ !MAX_WAIT! (
            echo.
            echo %Y%[ERROR] CopynDown did not close in time.%W%
            echo Please close CopynDown manually and run the updater again.
            pause
            exit /b 1
        )

        timeout /t 1 >nul
        goto wait_app
    )
)

echo %C%[%W%*%C%]%W% Status: %Y%Cleaning up legacy files...%W%
del /f /q "YT Video Downloader.bat" "YT Music Downloader.bat" "YT MP3 Converter.bat" "Insta Video Downloader.bat" "Auto Update.bat" >nul 2>&1
del /f /q "Readme (EN).txt" "Readme (PT).txt" "YT.Video.Downloader.zip" >nul 2>&1

echo %C%[%W%*%C%]%W% Status: %Y%Extracting new files...%W%

set "ZIP_FILE="
if exist "CopynDown_Windows.zip" set "ZIP_FILE=CopynDown_Windows.zip"
if exist "CopynDown.zip" set "ZIP_FILE=CopynDown.zip"

if not defined ZIP_FILE (
    echo.
    echo %Y%[ERROR] Update ZIP file was not found.%W%
    pause
    exit /b 1
)

if exist "certifi" (
    for %%D in ("certifi" "charset_normalizer" "cryptography" "customtkinter" "PIL" "tcl" "tcl8" "tk") do (
        if exist "%%~D" rmdir /s /q "%%~D" >nul 2>&1
    )

    del /f /q "_tkinter.pyd" "pyexpat.pyd" "python3.dll" "_asyncio.pyd" "_cffi_backend.pyd" "_multiprocessing.pyd" "_overlapped.pyd" >nul 2>&1
    del /f /q "bin\logo.png" "bin\icon.ico" >nul 2>&1

    set "DEST_PATH=.."
) else (
    if exist "bin" (
        robocopy "bin" "core\bin" /MOVE /E /IS >nul 2>&1

        if errorlevel 8 (
            echo.
            echo %Y%[ERROR] Failed to move existing bin folder.%W%
            pause
            exit /b 1
        )
    )

    set "DEST_PATH=."
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; Expand-Archive -LiteralPath '%ZIP_FILE%' -DestinationPath '%DEST_PATH%' -Force"

if errorlevel 1 (
    echo.
    echo %Y%[ERROR] Failed to extract update files.%W%
    pause
    exit /b 1
)

del /f /q "%ZIP_FILE%" >nul 2>&1

echo.
echo %G%-------------------------------------------------------%W%
echo   [SUCCESS] Update completed!
echo   Starting CopynDown...
echo %G%-------------------------------------------------------%W%
echo.

if exist "%DEST_PATH%\CopynDown.exe" (
    pushd "%DEST_PATH%"
    start "" "CopynDown.exe"
    popd
) else (
    echo.
    echo %Y%[WARNING] CopynDown.exe was not found after update.%W%
    echo Please open CopynDown manually.
    pause
)

timeout /t 2 >nul
start "" /b cmd /c "timeout /t 1 >nul & del /f /q ""%~f0"""
exit
