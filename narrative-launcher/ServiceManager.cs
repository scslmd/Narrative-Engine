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
}
