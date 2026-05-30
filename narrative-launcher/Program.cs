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

// Check if backend is already running
var backendRunning = await services.IsBackendRunningAsync();
if (backendRunning)
{
    Console.WriteLine("Backend already running, skipping start.");
    await services.AttachExternalBackendAsync();
}
else
{
    // Build frontend if needed, then start backend
    Console.WriteLine("Building frontend...");
    await services.StartFrontendAsync();
    Console.WriteLine("Starting backend...");
    services.StartBackend();
}

var monitor = new HealthMonitor(services, tray);
monitor.Start();

// Shared exit handler
var tcs = new TaskCompletionSource();
var exit = () =>
{
    if (tcs.Task.IsCompleted) return;
    tcs.SetResult();
};

// Wire status window with exit callback
var statusWindow = new StatusWindow(services, async () =>
{
    await services.StopAsync();
    exit();
});
tray.SetStatusWindow(statusWindow);

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
            await services.StartFrontendAsync();
            break;

        case "exit":
            await services.StopAsync();
            exit();
            break;
    }
};

// Wait for Exit (Ctrl+C or tray menu)
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    exit();
};

Console.WriteLine("Running. Right-click tray icon for menu. Ctrl+C to exit.");
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

static void RestartService(ServiceInfo service)
{
    if (service.Process is { HasExited: false } proc)
    {
        proc.Kill();
        proc.WaitForExit(2000);
    }
    service.Process = null;
}
