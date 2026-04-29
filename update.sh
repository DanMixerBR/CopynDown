#!/bin/bash

# 1. Pega o caminho ABSOLUTO de onde o script e o ZIP realmente estão
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SCRIPT_NAME="$(basename "$0")"

# 2. Se o terminal for invisível (chamado pelo Python), abre uma janela real
if [ ! -t 1 ]; then
    if command -v gnome-terminal &> /dev/null; then
        # Força o terminal novo a entrar na pasta correta antes de rodar!
        gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && bash '$SCRIPT_NAME'"
    elif command -v xterm &> /dev/null; then
        xterm -e bash -c "cd '$SCRIPT_DIR' && bash '$SCRIPT_NAME'"
    fi
    exit 0 # Mata o processo invisível antigo
fi

# 3. Garante que o terminal visível trabalhe dentro da pasta certa
cd "$SCRIPT_DIR" || exit

# =================================================================
# INTERFACE VISUAL E LÓGICA DE EXTRAÇÃO
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

# Extrai o zip uma pasta para trás (na raiz do app)
unzip -o CopynDown_Linux.zip -d .. > /dev/null 2>&1

# Deleta o arquivo zip após a extração
rm -f CopynDown_Linux.zip

echo ""
echo -e "${G}-------------------------------------------------------${W}"
echo "  [SUCCESS] Update completed!"
echo "  Please restart the app."
echo -e "${G}-------------------------------------------------------${W}"
echo ""

# Aguarda 5 segundos para o usuário ler a tela
sleep 5

# Lógica de auto-deleção à prova de falhas (usando o caminho absoluto)
rm -f "$SCRIPT_DIR/$SCRIPT_NAME"
