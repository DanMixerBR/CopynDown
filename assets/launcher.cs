using System.Diagnostics;
using System.IO;
using System;
using System.Reflection;

// ==========================================
// METADADOS DO LAUNCHER (VERSÃO INDEPENDENTE)
// ==========================================
[assembly: AssemblyTitle("CopynDown Launcher")]
[assembly: AssemblyDescription("CopynDown Launcher")]
[assembly: AssemblyCompany("DanMixerBR")]
[assembly: AssemblyProduct("CopynDown")]
[assembly: AssemblyCopyright("MIT License")]
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: AssemblyFileVersion("1.0.0.0")]

class Program {
    static void Main() {
        // Descobre onde o launcher está rodando
        string currentDir = AppDomain.CurrentDomain.BaseDirectory;
        
        // Aponta para o executável real escondido na pasta core
        string targetPath = Path.Combine(currentDir, "core", "CopynDown.exe");

        // Se o arquivo existir, ele executa
        if (File.Exists(targetPath)) {
            ProcessStartInfo info = new ProcessStartInfo();
            info.FileName = "cmd.exe";
            
            // Usando a soma tradicional de textos para máxima compatibilidade
            info.Arguments = "/c start \"\" \"" + targetPath + "\"";
            
            // Oculta completamente a janela preta do CMD
            info.WindowStyle = ProcessWindowStyle.Hidden;
            info.CreateNoWindow = true;
            
            // Dispara a execução e o launcher se auto-encerra
            Process.Start(info);
        }
    }
}