#include <windows.h>
#include <string.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char path[MAX_PATH];
    
    // Captura o caminho completo de onde o launcher está rodando
    GetModuleFileName(NULL, path, MAX_PATH);
    
    // Corta o "CopynDown.exe" do final para descobrirmos a pasta raiz
    char *lastSlash = strrchr(path, '\\');
    if (lastSlash) {
        *lastSlash = '\0';
    }
    
    // Anexa o caminho correto do executável principal
    strcat(path, "\\core\\CopynDown.exe");
    
    // Inicia o programa original de forma silenciosa e instantânea
    ShellExecute(NULL, "open", path, NULL, NULL, SW_SHOW);
    return 0;
}
