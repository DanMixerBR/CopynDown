#!/bin/bash

# ANSI Color Definitions
ESC="\e"
G="${ESC}[92m"
C="${ESC}[96m"
W="${ESC}[0m"
Y="${ESC}[93m"

clear
echo -e "${C}=======================================================${W}"
echo -e "          ${G}CopynDown${W} - ${Y}Update Manager${W}"
echo -e "${C}=======================================================${W}"
echo ""

echo -e "${C}[${W}*${C}]${W} Status: ${Y}Extracting new files...${W}"

unzip -o CopynDown_Linux.zip -d .. > /dev/null 2>&1

chmod +x CopynDown
chmod +x bin/yt-dlp
chmod +x bin/ffmpeg
chmod +x bin/deno

rm -f CopynDown_Linux.zip

echo ""
echo -e "${G}-------------------------------------------------------${W}"
echo "  [SUCCESS] Update completed!"
echo "  Please restart the app."
echo -e "${G}-------------------------------------------------------${W}"
echo ""

sleep 5

rm -- "$0"
