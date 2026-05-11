using System.Timers;
using System.Net.Http;

namespace NarrativeLauncher;

public class HealthMonitor
{
    private readonly ServiceManager _services;
    private readonly TrayManager _tray;
    private readonly HttpClient _http = new();
    private readonly System.Timers.Timer _timer;
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
        _timer = new System.Timers.Timer(5000); // 5 second polling interval
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
