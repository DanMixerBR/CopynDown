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
rmdir /s /q "bin" "core\certifi" "core\charset_normalizer" "core\customtkinter" "core\PIL" "core\tcl" "core\tcl8" "core\tk" >nul 2>&1
del /f /q "YT Video Downloader.bat" "YT Music Downloader.bat" "YT MP3 Converter.bat" "Insta Video Downloader.bat" "Auto Update.bat" >nul 2>&1
del /f /q "Readme (EN).txt" "Readme (PT).txt" "YT.Video.Downloader.zip" >nul 2>&1

echo %C%[%W%*%C%]%W% Status: %Y%Extracting new files...%W%
if exist "certifi" (
    if exist "CopynDown_Windows.zip" (
        powershell -command "Expand-Archive -Path 'CopynDown_Windows.zip' -DestinationPath '..' -Force"
        del /f /q "CopynDown_Windows.zip"
    ) else if exist "CopynDown.zip" (
        powershell -command "Expand-Archive -Path 'CopynDown.zip' -DestinationPath '..' -Force"
        del /f /q "CopynDown.zip"
    )
) else (
    if exist "CopynDown_Windows.zip" (
        powershell -command "Expand-Archive -Path 'CopynDown_Windows.zip' -DestinationPath '.' -Force"
        del /f /q "CopynDown_Windows.zip"
    ) else if exist "CopynDown.zip" (
        powershell -command "Expand-Archive -Path 'CopynDown.zip' -DestinationPath '.' -Force"
        del /f /q "CopynDown.zip"
    )
)

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
