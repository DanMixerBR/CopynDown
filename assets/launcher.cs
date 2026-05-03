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
        
        // Aponta para o executável real e para a pasta core
        string coreDir = Path.Combine(currentDir, "core");
        string targetPath = Path.Combine(coreDir, "CopynDown.exe");

        // Se o arquivo existir, ele executa
        if (File.Exists(targetPath)) {
            ProcessStartInfo info = new ProcessStartInfo();
            info.FileName = "cmd.exe";
            
            // =========================================================
            // A CORREÇÃO SIMPLES E CIRÚRGICA: 
            // Diz para o CMD abrir já enxergando a pasta "core" como base.
            // O programa herdará essa pasta e encontrará o "bin" corretamente!
            // =========================================================
            info.WorkingDirectory = coreDir;
            
            // Usando a soma tradicional de textos e mantendo o SEGREDO DO SMARTSCREEN
            // (Como o WorkingDirectory já é o coreDir, chamamos apenas o nome do executável)
            info.Arguments = "/c start \"\" \"CopynDown.exe\"";
            
            // Oculta completamente a janela preta do CMD
            info.WindowStyle = ProcessWindowStyle.Hidden;
            info.CreateNoWindow = true;
            
            // Dispara a execução e o launcher se auto-encerra
            Process.Start(info);
        }
    }
}