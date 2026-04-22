@echo off

powershell -command "Expand-Archive -Path 'CopynDown.zip' -DestinationPath '.' -Force"

del /f /q "YT Video Downloader.bat" "YT Music Downloader.bat" "YT MP3 Converter.bat" "Insta Video Downloader.bat" "Readme (EN).txt" "Readme (PT).txt" "YT.Video.Downloader.zip" "Auto Update.bat" "CopynDown.exe.old" "CopynDown.zip" "update.bat" >nul 2>&1

echo.
echo.
echo.
echo.
echo Update complete! Please restart the app.
echo.
echo.
echo.
echo.
timeout /t 5

exit
