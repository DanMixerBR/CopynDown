#!/bin/bash

# Garante que o script está rodando na pasta certa
cd "$(dirname "$0")" || exit

# =================================================================
# O PULO DO GATO: DETECÇÃO DE TERMINAL INVISÍVEL
# =================================================================
# O comando [ ! -t 1 ] verifica se o script NÃO tem uma tela conectada a ele.
if [ ! -t 1 ]; then
    # Se estiver invisível, ele tenta abrir o próprio script em um terminal real
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash "$0"
    elif command -v xterm &> /dev/null; then
        xterm -e bash "$0"
    else
        bash "$0" # Fallback: se o usuário tiver um Linux exótico sem terminal padrão
    fi
    exit 0 # Mata a versão invisível original
fi
# =================================================================

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

# Extrai o zip uma pasta para trás
unzip -o CopynDown_Linux.zip -d .. > /dev/null 2>&1

# Deleta o arquivo zip após a extração
rm -f CopynDown_Linux.zip

echo ""
echo -e "${G}-------------------------------------------------------${W}"
echo "  [SUCCESS] Update completed!"
echo "  Please restart the app."
echo -e "${G}-------------------------------------------------------${W}"
echo ""

# Agora a janela preta vai ficar visível por 5 segundos!
sleep 5

# Lógica de auto-deleção (Apaga o próprio script)
rm -- "$0"
