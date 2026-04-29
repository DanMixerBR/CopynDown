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

# Extrai o zip sobrescrevendo os arquivos antigos sem perguntar (-o)
unzip -o CopynDown.zip > /dev/null 2>&1

# Deleta o arquivo zip após a extração
rm -f CopynDown.zip

echo ""
echo -e "${G}-------------------------------------------------------${W}"
echo "  [SUCCESS] Update completed!"
echo "  Please restart the app."
echo -e "${G}-------------------------------------------------------${W}"
echo ""

# Aguarda 5 segundos (equivalente ao timeout do Windows)
sleep 5

# Lógica de auto-deleção (Apaga o próprio script)
rm -- "$0"
