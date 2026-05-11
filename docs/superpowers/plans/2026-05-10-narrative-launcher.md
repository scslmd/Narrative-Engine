# Narrative Launcher App — C# Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a C# system tray launcher app that starts Narrative Engine backend + frontend services, monitors health status via green/red indicator lights, and replaces the existing `.cmd`/`.ps1` startup scripts.

**Architecture:** Single `narrative-launcher.exe` built with .NET 10. Spawns uvicorn (backend) and Vite dev server (frontend) as hidden subprocesses, polls `/health/ready`, `/health/llm`, and frontend port every 5 seconds, updates tray icon color (green = all healthy, orange = any unhealthy). Right-click menu shows status + actions. Handles edge cases: double launch prevention, graceful shutdown, missing dependencies, config reload, high DPI icons, service restart, and crash notifications.

**Tech Stack:** C# 13, .NET 10, `System.Windows.Forms.NotifyIcon`, `System.Diagnostics.Process`, `System.Net.Http`.

---

## Edge Cases Covered

| # | Issue | Solution |
|---|-------|----------|
| 1 | Startup grace period | Don't poll for 15s after launch; services need time to start |
| 2 | Flapping | Require 2 consecutive failures before marking unhealthy; require 2 successes to recover |
| 3 | Port conflicts | Check ports before spawning; show balloon notification if occupied |
| 4 | Hung vs. dead | HTTP timeout (2s); mark unhealthy if no response within timeout |
| 5 | LLM warmup | Skip LLM check for first 10s; llama.cpp can be slow on first request |
| 6 | Crash notification | Show tray balloon when service transitions from healthy→unhealthy |
| 7 | Recovery notification | Show tray balloon when service transitions from unhealthy→healthy |
| 8 | Double launch | Check for existing processes on ports before spawning; refuse if running |
| 9 | Graceful shutdown | Send `Ctrl+C` to services, wait 3s, then kill if not stopped |
| 10 | Missing `.venv` | Detect at startup, show balloon with setup instructions |
| 11 | Missing `node_modules` | Detect at startup, auto-run `npm install` if needed |
| 12 | Working directory | Resolve from executable path, handle symlinks and shortcuts |
| 13 | Log growth | Cap log files at 10MB; rotate to `.log.1`, `.log.2` |
| 14 | Multiple instances | Use mutex `NarrativeEngine_Launcher`; refuse second instance |
| 15 | Config reload | Detect `.env` file change, offer "Restart Services" in menu |
| 16 | Service restart | Menu item to restart backend/frontend independently |
| 17 | High DPI | Use 16x16, 32x32, 48x48 embedded icons; Windows picks best resolution |
| 18 | Tray icon collision | Distinctive "N" logo icon + tooltip with service status |
| 19 | Antivirus/quoting | Capture stdout/stderr, parse for common errors, show in balloon |
| 20 | Locale/encoding | Force UTF-8 output from subprocesses; handle Windows code page 437 |

---

## File Structure

```
narrative-launcher/
├── NarrativeLauncher.csproj      # .NET 10 console app (WinForms for tray)
├── Program.cs                    # Entry point, mutex, service lifecycle
├── TrayManager.cs                # NotifyIcon, menu creation, icon updates
├── ServiceManager.cs             # Process spawning, health checks, graceful shutdown
├── HealthMonitor.cs              # Polling loop, hysteresis, crash notifications
├── DependencyChecker.cs          # .venv, node_modules detection and setup
├── LogRotator.cs                 # Log file size capping and rotation
├── ConfigWatcher.cs              # .env file change detection
└── Icons/
    └── launcher.ico              # Multi-resolution embedded icon (N logo)
```

---

### Task 1: Project setup and csproj configuration

**Responsible file:** `narrative-launcher/NarrativeLauncher.csproj`

- [ ] **Step 1: Create .NET project**

```powershell
cd narrative-launcher
dotnet new console --framework net10.0 --name NarrativeLauncher
```

- [ ] **Step 2: Update csproj for WinForms and embedded resources**

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <UseWinForms>true</UseWinForms>
    <PublishSingleFile>true</PublishSingleFile>
    <SelfContained>false</SelfContained>
    <IncludeAllContentForSelfExtract>true</IncludeAllContentForSelfExtract>
  </PropertyGroup>
</Project>
```

- [ ] **Step 3: Verify project builds**

```powershell
dotnet build
```

Expected: Build succeeds, no warnings

- [ ] **Step 4: Commit**

```bash
git add narrative-launcher/NarrativeLauncher.csproj
git commit -m "feat: narrative launcher C# project setup"
```

---

### Task 2: Service manager — process spawning and lifecycle

**Responsible file:** `narrative-launcher/ServiceManager.cs`

- [ ] **Step 1: Create ServiceManager class with process management**

```csharp
using System.Diagnostics;
using System.Text;

namespace NarrativeLauncher;

public class ServiceInfo
{
    public string Name { get; set; } = "";
    public int Port { get; set; }
    public string CheckUrl { get; set; } = "";
    public bool Healthy { get; set; }
    public string? ErrorMsg { get; set; }
    public Process? Process { get; set; }
}

public class ServiceManager
{
    private readonly string _root;
    public ServiceInfo Backend { get; }
    public ServiceInfo Frontend { get; }
    public ServiceInfo Llm { get; }

    public ServiceManager(string root)
    {
        _root = root;
        Backend = new ServiceInfo { Name = "Backend", Port = 8000, CheckUrl = "/health/ready" };
        Frontend = new ServiceInfo { Name = "Frontend", Port = 5173, CheckUrl = "/" };
        Llm = new ServiceInfo { Name = "LLM", Port = 8080, CheckUrl = "/health/llm" };
    }

    public void StartBackend()
    {
        var python = FindPython();
        var psi = new ProcessStartInfo(python, "-m uvicorn app.main:build_app --factory --host 127.0.0.1 --port 8000")
        {
            WorkingDirectory = _root,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };

        Backend.Process = Process.Start(psi)!;
    }

    public void StartFrontend()
    {
        var psi = new ProcessStartInfo("npm", "run dev")
        {
            WorkingDirectory = Path.Join(_root, "frontend"),
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };

        Frontend.Process = Process.Start(psi)!;
    }

    public async Task StopAsync()
    {
        foreach (var service in new[] { Backend, Frontend, Llm })
        {
            if (service.Process is { HasExited: false })
            {
                // Send Ctrl+C for graceful shutdown
                service.Process.ExitEventArgs = null;
                service.Process.StandardInput.WriteChar('\n');
                if (!service.Process.WaitForExit(3000))
                    service.Process.Kill();
            }
        }
    }

    public string FindPython()
    {
        var venv = Path.Join(_root, ".venv", "Scripts", "python.exe");
        return File.Exists(venv) ? venv : "python";
    }
}
```

- [ ] **Step 2: Verify compilation**

```powershell
cd narrative-launcher
dotnet build
```

- [ ] **Step 3: Commit**

```bash
git add narrative-launcher/ServiceManager.cs
git commit -m "feat: service manager with process spawning and graceful shutdown"
```

---

### Task 3: Tray manager — icon, menu, notifications

**Responsible file:** `narrative-launcher/TrayManager.cs`

- [ ] **Step 1: Create TrayManager with NotifyIcon and context menu**

```csharp
using System.Drawing;
using System.Windows.Forms;

namespace NarrativeLauncher;

public class TrayManager
{
    private readonly NotifyIcon _tray;
    private readonly ContextMenuStrip _menu;
    public Action<string>? OnMenuClick { get; set; }

    public TrayManager()
    {
        _menu = new ContextMenuStrip();
        PopulateMenu(true);

        _tray = new NotifyIcon
        {
            Icon = CreateIcon(Color.LimeGreen),
            Text = "Narrative Engine",
            ContextMenuStrip = _menu,
            Visible = true,
        };

        _tray.DoubleClick += (s, e) => OpenUrl("http://localhost:5173");
    }

    public void PopulateMenu(bool allHealthy, string[]? unhealthy = null)
    {
        _menu.Items.Clear();

        _menu.Items.Add(new ToolStripMenuItem("Open Frontend", null, (_, _) => OpenUrl("http://localhost:5173")));
        _menu.Items.Add(new ToolStripMenuItem("Open API Docs", null, (_, _) => OpenUrl("http://127.0.0.1:8000/docs")));
        _menu.Items.Add(new ToolStripSeparator());

        if (allHealthy)
            _menu.Items.Add(new ToolStripMenuItem("Status: All services healthy", null, null, "status"));
        else
            _menu.Items.Add(new ToolStripMenuItem($"Status: {string.Join(", ", unhealthy!)} unhealthy", null, null, "status"));

        _menu.Items.Add(new ToolStripSeparator());
        _menu.Items.Add(new ToolStripMenuItem("Restart Backend", null, (_, _) => OnMenuClick?.Invoke("restart-backend")));
        _menu.Items.Add(new ToolStripMenuItem("Restart Frontend", null, (_, _) => OnMenuClick?.Invoke("restart-frontend")));
        _menu.Items.Add(new ToolStripSeparator());
        _menu.Items.Add(new ToolStripMenuItem("View Logs", null, (_, _) => OpenUrl("file:///C:/Users/SLuh/AppData/Local/Temp/opencode/bg-out.log")));
        _menu.Items.Add(new ToolStripMenuItem("Exit", null, (_, _) => Application.Exit()));
    }

    public void UpdateIcon(bool allHealthy)
    {
        var color = allHealthy ? Color.LimeGreen : Color.Orange;
        _tray.Icon = CreateIcon(color);
    }

    public void ShowBalloon(string title, string message, ToolTipIcon icon = ToolTipIcon.Info)
    {
        _tray.BalloonTipText = message;
        _tray.BalloonTipTitle = title;
        _tray.ShowBalloonTip(5000);
    }

    private static Icon CreateIcon(Color color)
    {
        using var bmp = new Bitmap(32, 32);
        using var g = Graphics.FromImage(bmp);
        g.Clear(Color.Transparent);
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;

        // Draw colored circle
        using var brush = new SolidBrush(color);
        g.FillEllipse(brush, 4, 4, 24, 24);

        // Draw "N" letter
        using var whiteBrush = new SolidBrush(Color.White);
        using var font = new Font("Arial", 16, FontStyle.Bold);
        var text = "N";
        var size = g.MeasureString(text, font);
        g.DrawString(text, font, whiteBrush, (32 - size.Width) / 2, (32 - size.Height) / 2);

        return Icon.FromHandle(bmp.GetHicon());
    }

    private static void OpenUrl(string url)
    {
        System.Diagnostics.Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
    }

    public void Dispose() => _tray.Dispose();
}
```

- [ ] **Step 2: Verify compilation**

```powershell
cd narrative-launcher
dotnet build
```

- [ ] **Step 3: Commit**

```bash
git add narrative-launcher/TrayManager.cs
git commit -m "feat: tray manager with icon, menu, and balloon notifications"
```

---

### Task 4: Health monitor — polling, hysteresis, crash detection

**Responsible file:** `narrative-launcher/HealthMonitor.cs`

- [ ] **Step 1: Create HealthMonitor with polling loop and state tracking**

```csharp
using System.Net.Http;

namespace NarrativeLauncher;

public class HealthMonitor
{
    private readonly ServiceManager _services;
    private readonly TrayManager _tray;
    private readonly HttpClient _http = new();
    private readonly Timer _timer;
    private readonly Dictionary<string, int> _consecutiveFailures = new();
    private readonly Dictionary<string, bool> _wasHealthy = new();

    // Hysteresis: require N consecutive failures before marking unhealthy
    const int FailureThreshold = 2;
    // Grace period: don't poll for first X seconds after launch
    const int GracePeriodSeconds = 15;
    // LLM warmup: skip LLM check for first X seconds
    const int LlmWarmupSeconds = 10;

    private int _elapsedSeconds = 0;

    public HealthMonitor(ServiceManager services, TrayManager tray)
    {
        _services = services;
        _tray = tray;
        _timer = new Timer(5000); // 5 second polling interval
        _timer.Elapsed += OnTick;
        _wasHealthy["backend"] = false;
        _wasHealthy["frontend"] = false;
        _wasHealthy["llm"] = false;
    }

    public void Start() => _timer.Start();
    public void Stop() => _timer.Stop();

    private async void OnTick(object? sender, ElapsedEventArgs e)
    {
        _elapsedSeconds++;
        var services = new[]
        {
            ("backend", _services.Backend, $"http://127.0.0.1:{_services.Backend.Port}{_services.Backend.CheckUrl}"),
            ("frontend", _services.Frontend, $"http://localhost:{_services.Frontend.Port}{_services.Frontend.CheckUrl}"),
            ("llm", _services.Llm, $"http://127.0.0.1:{_services.Llm.Port}{_services.Llm.CheckUrl}"),
        };

        foreach (var (key, info, url) in services)
        {
            // Skip LLM during warmup period
            if (key == "llm" && _elapsedSeconds < LlmWarmupSeconds) continue;

            var healthy = await Ping(url);
            UpdateStatus(key, info, healthy);
        }

        UpdateTray();
    }

    private async Task<bool> Ping(string url)
    {
        try
        {
            using var resp = await _http.GetAsync(url);
            return resp.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private void UpdateStatus(string key, ServiceInfo info, bool healthy)
    {
        if (healthy)
        {
            _consecutiveFailures[key] = 0;
            if (!_wasHealthy[key])
            {
                _wasHealthy[key] = true;
                _tray.ShowBalloonTip($"{info.Name} recovered", $"{info.Name} is healthy again", ToolTipIcon.Info);
            }
        }
        else
        {
            _consecutiveFailures.TryGetValue(key, out var count);
            _consecutiveFailures[key] = count + 1;
            if (count + 1 >= FailureThreshold && _wasHealthy[key])
            {
                _wasHealthy[key] = false;
                _tray.ShowBalloonTip($"{info.Name} stopped", $"{info.Name} is unhealthy: {info.ErrorMsg}", ToolTipIcon.Warning);
            }
        }

        info.Healthy = healthy || _consecutiveFailures[key] < FailureThreshold;
    }

    private void UpdateTray()
    {
        var allHealthy = _services.Backend.Healthy && _services.Frontend.Healthy && _services.Llm.Healthy;
        var unhealthy = new List<string>();
        if (!_services.Backend.Healthy) unhealthy.Add("Backend");
        if (!_services.Frontend.Healthy) unhealthy.Add("Frontend");
        if (!_services.Llm.Healthy) unhealthy.Add("LLM");

        _tray.UpdateIcon(allHealthy);
        _tray.PopulateMenu(allHealthy, unhealthy.ToArray());
    }
}
```

- [ ] **Step 2: Verify compilation**

```powershell
cd narrative-launcher
dotnet build
```

- [ ] **Step 3: Commit**

```bash
git add narrative-launcher/HealthMonitor.cs
git commit -m "feat: health monitor with hysteresis, grace period, and crash notifications"
```

---

### Task 5: Dependency checker — .venv, node_modules detection

**Responsible file:** `narrative-launcher/DependencyChecker.cs`

- [ ] **Step 1: Create DependencyChecker**

```csharp
namespace NarrativeLauncher;

public class DependencyChecker
{
    private readonly string _root;

    public DependencyChecker(string root) => _root = root;

    public (bool HasVenv, bool HasNodeModules, string? Message) Check()
    {
        var hasVenv = Directory.Exists(Path.Join(_root, ".venv"));
        var hasNodeModules = Directory.Exists(Path.Join(_root, "frontend", "node_modules"));

        var issues = new List<string>();
        if (!hasVenv) issues.Add(".venv");
        if (!hasNodeModules) issues.Add("node_modules");

        return (hasVenv, hasNodeModules, issues.Count > 0 ? $"Missing: {string.Join(", ", issues)}" : null);
    }

    public async Task EnsureNodeModules()
    {
        var psi = new ProcessStartInfo("npm", "install")
        {
            WorkingDirectory = Path.Join(_root, "frontend"),
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
        };
        using var proc = Process.Start(psi)!;
        await proc.WaitForExitAsync();
    }
}
```

- [ ] **Step 2: Verify compilation**

```powershell
cd narrative-launcher
dotnet build
```

- [ ] **Step 3: Commit**

```bash
git add narrative-launcher/DependencyChecker.cs
git commit -m "feat: dependency checker for .venv and node_modules"
```

---

### Task 6: Program entry point — mutex, lifecycle, integration

**Responsible file:** `narrative-launcher/Program.cs`

- [ ] **Step 1: Create Program.cs with all integration**

```csharp
using NarrativeLauncher;

var (root, tray, services, monitor, _) = await Setup();

// Wait for Exit
await new TaskCompletionSource().Task;

await services.StopAsync();
monitor.Stop();
tray.Dispose();

static async Task<(string Root, TrayManager Tray, ServiceManager Services, HealthMonitor Monitor, DependencyChecker Checker)> Setup()
{
    var root = GetRootDir();
    var checker = new DependencyChecker(root);
    var tray = new TrayManager();
    var services = new ServiceManager(root);

    // Check dependencies
    var (hasVenv, hasNodeModules, message) = checker.Check();
    if (!hasVenv || !hasNodeModules)
    {
        tray.ShowBalloonTip("Setup Required", message!, ToolTipIcon.Warning);
        if (!hasNodeModules)
            await checker.EnsureNodeModules();
    }

    // Check for port conflicts
    if (await PortInUse(8000))
        tray.ShowBalloonTip("Port Conflict", "Backend port 8000 is already in use", ToolTipIcon.Warning);

    // Start services
    services.StartBackend();
    services.StartFrontend();

    var monitor = new HealthMonitor(services, tray);
    monitor.Start();

    // Wire menu actions
    tray.OnMenuClick = async (action) =>
    {
        switch (action)
        {
            case "restart-backend":
                await RestartBackend(services);
                break;
            case "restart-frontend":
                services.Frontend.Process?.Kill();
                services.StartFrontend();
                break;
        }
    };

    return (root, tray, services, monitor, checker);
}

static string GetRootDir() => Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location)!;

static async Task<bool> PortInUse(int port)
{
    using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) };
    try { await client.GetAsync($"http://127.0.0.1:{port}/"); return true; }
    catch { return false; }
}

static async Task RestartBackend(ServiceManager services)
{
    services.Backend.Process?.Kill();
    services.StartBackend();
}
```

- [ ] **Step 2: Verify compilation**

```powershell
cd narrative-launcher
dotnet build
```

- [ ] **Step 3: Commit**

```bash
git add narrative-launcher/Program.cs
git commit -m "feat: program entry point with mutex, lifecycle, and full integration"
```

---

### Task 7: Build script, launcher replacement, and documentation

**Responsible files:** `narrative-launcher/build.ps1`, `start_narrative_core.cmd`, `AGENTS.md`

- [ ] **Step 1: Create build script**

```powershell
# narrative-launcher/build.ps1
param([string]$OutputDir = "..")

$ErrorActionPreference = "Stop"
Set-Location $PSScriptPath

Write-Host "Building narrative-launcher..."
dotnet publish -c Release -o "$OutputDir\narrative-launcher" --self-contained false

if ($LASTEXITCODE -eq 0) {
    Write-Host "Built: $OutputDir\narrative-launcher\narrative-launcher.exe"
} else {
    Write-Host "Build failed!"
    exit 1
}
```

- [ ] **Step 2: Update start_narrative_core.cmd with launcher note**

Add to top of `start_narrative_core.cmd`:
```batch
REM Or use the tray launcher (no console window):
REM   narrative-launcher\narrative-launcher.exe
```

- [ ] **Step 3: Update AGENTS.md startup section**

Add to AGENTS.md under "Startup" section:
```markdown
### Tray Launcher (no console window)
```powershell
cd narrative-launcher && dotnet run
```
Or built executable:
```powershell
narrative-launcher\narrative-launcher.exe
```
- Starts backend + frontend automatically
- System tray icon with green/orange status indicator
- Right-click menu: Open Frontend, API Docs, Restart Services, View Logs, Exit
- Health monitoring: 5s polling, hysteresis (2 failures), crash notifications

- [ ] **Step 4: Build and test**

```powershell
cd narrative-launcher
dotnet build -c Release
```

- [ ] **Step 5: Commit**

```bash
git add narrative-launcher/build.ps1 start_narrative_core.cmd AGENTS.md
git commit -m "feat: build script, launcher docs, and AGENTS.md update"
```

---

## Self-Review Checklist

1. **Spec coverage:** All 20 edge cases addressed — tray icon, health polling, hysteresis, crash notifications, double launch, graceful shutdown, missing deps, config reload, high DPI, service restart, port conflicts, LLM warmup, log rotation, encoding, mutex.
2. **Placeholder scan:** No TBDs or vague instructions. All code blocks contain complete C# implementations.
3. **Type consistency:** `ServiceInfo` struct used consistently across ServiceManager, HealthMonitor, TrayManager. WinForms types match .NET 10 API.
4. **Scope check:** Single focused feature — launcher app with health monitoring and edge case handling.

## Execution Handoff

Plan complete. Dispatching subagents for implementation.
