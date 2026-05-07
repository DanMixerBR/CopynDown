#include <windows.h>
#include <string.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char baseDir[MAX_PATH];
    char coreDir[MAX_PATH];
    char targetPath[MAX_PATH];
    
    // Descobre onde o launcher está rodando
    GetModuleFileName(NULL, baseDir, MAX_PATH);
    char *lastSlash = strrchr(baseDir, '\\');
    if (lastSlash) *lastSlash = '\0';
    
    // Aponta para a pasta core (Path.Combine)
    strcpy(coreDir, baseDir);
    strcat(coreDir, "\\core");
    
    // Aponta para o executável real (Path.Combine)
    strcpy(targetPath, coreDir);
    strcat(targetPath, "\\CopynDown.exe");
    
    // Se o arquivo existir, ele executa (O equivalente ao File.Exists)
    if (GetFileAttributes(targetPath) != INVALID_FILE_ATTRIBUTES) {
        
        // Dispara o CMD oculto (SW_HIDE), passando o coreDir como base, 
        // e chamando apenas o nome do arquivo, mantendo o Segredo do SmartScreen!
        ShellExecute(NULL, "open", "cmd.exe", "/c start \"\" \"CopynDown.exe\"", coreDir, SW_HIDE);
    }
    
    return 0;
}
