#!/bin/bash

# ======================================================================
# Auto-Launch in Terminal
# Verifica se NÃO está rodando interativamente (sem TTY)
# ======================================================================
if [ ! -t 0 ]; then
    # Procura pelos terminais padrão do Fedora (Ptyxis no F40, GNOME Console no F39, GNOME Terminal)
    for term in ptyxis kgx gnome-terminal xterm; do
        if command -v "$term" >/dev/null 2>&1; then
            # gnome-terminal e ptyxis usam '--', kgx usa '-e'
            if [ "$term" = "gnome-terminal" ] || [ "$term" = "ptyxis" ]; then
                exec "$term" -- bash -c "\"$0\""
            else
                exec "$term" -e bash -c "\"$0\""
            fi
            exit 0
        fi
    done
fi

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
chmod +x bin/ffprobe
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
