using System.Diagnostics;
using NarrativeLauncher;

// Mutex to prevent double launch
var mutex = new Mutex(true, "Global\\NarrativeEngine-Launcher", out var isFirst);
if (!isFirst)
{
    return;
}

var root = GetRootDir();
var checker = new DependencyChecker(root);
var services = new ServiceManager(root);
var tray = new TrayManager(services);

// Check dependencies
var (hasVenv, hasNodeModules, message) = checker.Check();
if (!hasVenv || !hasNodeModules)
{
    tray.ShowBalloonTip("Setup Required", message!, ToolTipIcon.Warning);
    if (!hasNodeModules)
        await checker.EnsureNodeModules();

    (_, hasNodeModules, _) = checker.Check();
}

// Check for port conflicts
if (await PortInUse(8000))
    tray.ShowBalloonTip("Port Conflict", "Backend port 8000 is already in use", ToolTipIcon.Warning);

// Start services
Console.WriteLine("Starting backend and frontend...");
services.StartBackend();
services.StartFrontend();

var monitor = new HealthMonitor(services, tray);
monitor.Start();
Console.WriteLine("Running. Right-click tray icon for menu. Ctrl+C to exit.");

// Wire menu actions
tray.OnMenuClick = async (action) =>
{
    switch (action)
    {
        case "restart-backend":
            RestartService(services.Backend);
            services.StartBackend();
            break;

        case "restart-frontend":
            RestartService(services.Frontend);
            services.StartFrontend();
            break;
    }
};

// Wait for Exit (Ctrl+C or tray menu)
var tcs = new TaskCompletionSource();
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    tcs.SetResult();
};
await tcs.Task;

await services.StopAsync();
monitor.Stop();
tray.Dispose();
mutex.Dispose();

static string GetRootDir()
{
    var dir = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location)!;
    // Walk up to find project root (look for AGENTS.md or .git)
    while (dir != null)
    {
        if (File.Exists(Path.Join(dir, "AGENTS.md")) || Directory.Exists(Path.Join(dir, ".git")))
            return dir;
        dir = Path.GetDirectoryName(dir);
    }
    return Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location)!;
}

static async Task<bool> PortInUse(int port)
{
    using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) };
    try { await client.GetAsync($"http://127.0.0.1:{port}/"); return true; }
    catch { return false; }
}

static void RestartService(ServiceInfo service)
{
    if (service.Process is { HasExited: false } proc)
    {
        proc.Kill();
        proc.WaitForExit(2000);
    }
    service.Process = null;
}
