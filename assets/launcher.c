#include <windows.h>
#include <string.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char exePath[MAX_PATH];
    char coreDir[MAX_PATH]; // Nova variável para guardar o diretório de trabalho
    
    // Captura o caminho completo de onde o launcher está rodando
    GetModuleFileName(NULL, exePath, MAX_PATH);
    
    // Corta o "Launcher.exe" do final para descobrirmos a pasta raiz
    char *lastSlash = strrchr(exePath, '\\');
    if (lastSlash) {
        *lastSlash = '\0';
    }
    
    // 1. Cria o caminho exato da pasta "core" para ser o nosso Working Directory
    strcpy(coreDir, exePath);
    strcat(coreDir, "\\core");
    
    // 2. Anexa o caminho correto do executável principal
    strcat(exePath, "\\core\\CopynDown.exe"); 
    
    // 3. A MÁGICA: Inicia o programa passando o 'coreDir' no penúltimo parâmetro!
    ShellExecute(NULL, "open", exePath, NULL, coreDir, SW_SHOW);
    return 0;
}
