#include <windows.h>
#include <stdio.h> // Biblioteca padrão para usar o snprintf

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char baseDir[MAX_PATH];
    char coreDir[MAX_PATH];
    char targetPath[MAX_PATH];
    
    // Descobre onde o launcher está rodando
    GetModuleFileName(NULL, baseDir, MAX_PATH);
    char *lastSlash = strrchr(baseDir, '\\');
    if (lastSlash) *lastSlash = '\0';
    
    // snprintf junta os caminhos e limita o tamanho máximo por segurança (Substitui strcpy e strcat)
    snprintf(coreDir, MAX_PATH, "%s\\core", baseDir);
    snprintf(targetPath, MAX_PATH, "%s\\core\\CopynDown.exe", baseDir);
    
    // Se o arquivo existir, ele executa (Trava de Segurança Mantida!)
    if (GetFileAttributes(targetPath) != INVALID_FILE_ATTRIBUTES) {
        
        // Dispara o CMD oculto (SW_HIDE), passando o coreDir como base
        ShellExecute(NULL, "open", "cmd.exe", "/c start \"\" \"CopynDown.exe\"", coreDir, SW_HIDE);
    }
    
    return 0;
}
