@echo off
cls

:: Cores ANSI (Definições)
set "ESC="
set "G=%ESC%[92m"
set "C=%ESC%[96m"
set "W=%ESC%[0m"
set "Y=%ESC%[93m"

echo %C%=======================================================%W%
echo           %G%CopynDown%W% - %Y%Gerenciador de Atualizacao%W%
echo %C%=======================================================%W%
echo.
echo %C%[%W%*%C%]%W% Status: %Y%Extraindo novos arquivos...%W%
powershell -command "Expand-Archive -Path 'CopynDown.zip' -DestinationPath '.' -Force"

echo %C%[%W%*%C%]%W% Status: %Y%Limpando arquivos obsoletos...%W%
del /f /q "YT Video Downloader.bat" "YT Music Downloader.bat" "YT MP3 Converter.bat" "Insta Video Downloader.bat" "Readme (EN).txt" "Readme (PT).txt" "YT.Video.Downloader.zip" "CopynDown.zip" "CopynDown.exe.old" "bin\update.bat" "Auto Update.bat" >nul 2>&1

echo.
echo %G%-------------------------------------------------------%W%
echo   [OK] Atualizacao concluida com sucesso!
echo   Pressione qualquer tecla para reiniciar o app.
echo %G%-------------------------------------------------------%W%
echo.

pause >nul
:: Comando para se auto-deletar e sair
start /b "" cmd /c "timeout /t 1 >nul & del /f /q "%~f0""
exit
