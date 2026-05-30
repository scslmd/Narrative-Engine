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
    public int? ExternalPid { get; set; }
}

public class DuplicateProcess
{
    public int Pid { get; set; }
    public string Name { get; set; } = "";
    public int Port { get; set; }
}

public class ServiceManager
{
    private readonly string _root;
    public ServiceInfo Backend { get; }
    public ServiceInfo Frontend { get; }
    public ServiceInfo Llm { get; }
    public bool MonitorLlm { get; }

    public ServiceManager(string root)
    {
        _root = root;
        Backend = new ServiceInfo { Name = "Backend", Port = 8000, CheckUrl = "/health/ready" };
        Frontend = new ServiceInfo { Name = "Frontend", Port = 8000, CheckUrl = "/" };
        Llm = new ServiceInfo { Name = "LLM", Port = 8080, CheckUrl = "/health/llm" };
        MonitorLlm = false;
        Llm.Healthy = true;
    }

    public DuplicateProcess[] FindDuplicates()
    {
        var duplicates = new List<DuplicateProcess>();
        AddPortDuplicate(duplicates, Backend, Backend.Port);
        if (MonitorLlm)
            AddPortDuplicate(duplicates, Llm, Llm.Port);
        return duplicates.ToArray();
    }

    public void KillProcess(int pid)
    {
        var proc = Process.GetProcessById(pid);
        proc.Kill();
        proc.WaitForExit(2000);
    }

    public void StartBackend()
    {
        Backend.ExternalPid = null;
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

        var proc = Process.Start(psi)!;
        _ = Task.WhenAll(
            ReadAllAsync(proc.StandardOutput),
            ReadAllAsync(proc.StandardError));
        Backend.Process = proc;
    }

    public bool FrontendBuilt()
    {
        return File.Exists(Path.Join(_root, "frontend", "dist", "index.html"));
    }

    public async Task<bool> StartFrontendAsync(bool forceRebuild = false)
    {
        if (!forceRebuild && FrontendBuilt())
        {
            Console.WriteLine("Frontend already built, skipping.");
            return true;
        }

        var psi = new ProcessStartInfo("npm", "run build")
        {
            WorkingDirectory = Path.Join(_root, "frontend"),
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };

        var proc = Process.Start(psi)!;
        await Task.WhenAll(
            ReadAllAsync(proc.StandardOutput),
            ReadAllAsync(proc.StandardError));
        await proc.WaitForExitAsync();
        Frontend.Process = proc;
        return proc.ExitCode == 0;
    }

    public async Task<bool> IsBackendRunningAsync()
    {
        try
        {
            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) };
            using var resp = await client.GetAsync($"http://127.0.0.1:{Backend.Port}{Backend.CheckUrl}");
            return resp.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public bool IsFrontendReady()
    {
        return FrontendBuilt();
    }

    public bool IsLlmMonitored()
    {
        return MonitorLlm;
    }

    public async Task AttachExternalBackendAsync()
    {
        var pids = GetPidsListeningOnPort(Backend.Port);
        var pidList = pids.ToList();
        if (pidList.Count == 1)
        {
            Backend.ExternalPid = pidList[0];
        }
        else if (pidList.Count > 1)
        {
            Backend.ExternalPid = pidList[0];
        }
    }

    private static void AddPortDuplicate(List<DuplicateProcess> duplicates, ServiceInfo service, int port)
    {
        foreach (var pid in GetPidsListeningOnPort(port))
        {
            if (service.Process != null && pid == service.Process.Id)
                continue;
            if (service.ExternalPid.HasValue && pid == service.ExternalPid.Value)
                continue;

            var name = "Unknown";
            try
            {
                name = Process.GetProcessById(pid).ProcessName;
            }
            catch
            {
                // Ignore process lookup failures and keep best effort name.
            }

            duplicates.Add(new DuplicateProcess
            {
                Pid = pid,
                Name = $"{service.Name} ({name})",
                Port = port,
            });
        }
    }

    private static HashSet<int> GetPidsListeningOnPort(int port)
    {
        var pids = new HashSet<int>();
        var psi = new ProcessStartInfo("netstat", "-ano -p tcp")
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };

        using var proc = Process.Start(psi);
        if (proc == null)
            return pids;

        var output = proc.StandardOutput.ReadToEnd();
        proc.WaitForExit(2000);

        var suffix = $":{port}";
        foreach (var line in output.Split('\n', StringSplitOptions.RemoveEmptyEntries))
        {
            var trimmed = line.Trim();
            if (!trimmed.StartsWith("TCP", StringComparison.OrdinalIgnoreCase))
                continue;

            var parts = trimmed.Split((char[])null!, StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length < 5)
                continue;

            var localAddress = parts[1];
            var state = parts[3];
            if (!localAddress.EndsWith(suffix, StringComparison.Ordinal))
                continue;
            if (!string.Equals(state, "LISTENING", StringComparison.OrdinalIgnoreCase))
                continue;
            if (int.TryParse(parts[4], out var pid))
                pids.Add(pid);
        }

        return pids;
    }

    private static async Task ReadAllAsync(StreamReader reader)
    {
        await reader.ReadToEndAsync();
    }

    public async Task StopAsync()
    {
        foreach (var service in new[] { Backend, Frontend, Llm })
        {
            if (service.Process is { HasExited: false })
            {
                try
                {
                    // Send Ctrl+C for graceful shutdown
                    service.Process.StandardInput.Write('\n');
                    if (!service.Process.WaitForExit(3000))
                        service.Process.Kill();
                }
                catch
                {
                    service.Process.Kill();
                }
            }
        }
    }

    public string FindPython()
    {
        var venv = Path.Join(_root, ".venv", "Scripts", "python.exe");
        return File.Exists(venv) ? venv : "python";
    }

    public void RestartBackend()
    {
        if (Backend.Process is { HasExited: false } proc)
        {
            proc.Kill();
            proc.WaitForExit(2000);
        }
        Backend.Process = null;
        StartBackend();
    }

    public async Task RestartFrontendAsync()
    {
        if (Frontend.Process is { HasExited: false } proc)
        {
            proc.Kill();
            proc.WaitForExit(2000);
        }
        Frontend.Process = null;
        await StartFrontendAsync(forceRebuild: true);
    }

    public void KillAllDuplicates()
    {
        var duplicates = FindDuplicates();
        foreach (var dup in duplicates)
            KillProcess(dup.Pid);
    }

    public void ViewLogs()
    {
        var path = Path.Join(Environment.GetEnvironmentVariable("LOCALAPPDATA")!, "Temp", "opencode", "bg-out.log");
        _ = System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(path) { UseShellExecute = true });
    }
}
