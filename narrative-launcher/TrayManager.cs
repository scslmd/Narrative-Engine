using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;

namespace NarrativeLauncher;

public class TrayManager
{
    // Hidden control for thread marshaling
    private readonly Control _marshaler = new();
    private readonly NotifyIcon _tray;
    private readonly ContextMenuStrip _menu;
    private Icon? _currentIcon;
    public Action<string>? OnMenuClick { get; set; }
    private StatusWindow? _statusWindow;

    public TrayManager(ServiceManager services)
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

        _tray.DoubleClick += (s, e) => ShowStatusWindow(services);
    }

    private void ShowStatusWindow(ServiceManager services)
    {
        if (_statusWindow == null)
        {
            _statusWindow = new StatusWindow(services);
        }
        else
        {
            _statusWindow.Refresh();
        }
        _statusWindow.Show();
        _statusWindow.BringToFront();
    }

    public void PopulateMenu(bool allHealthy, string[]? unhealthy = null)
    {
        _menu.Items.Clear();

        _menu.Items.Add(new ToolStripMenuItem("Open Frontend", null,
            (_, _) => OpenUrl("http://localhost:5173")));
        _menu.Items.Add(new ToolStripMenuItem("Open API Docs", null,
            (_, _) => OpenUrl("http://127.0.0.1:8000/docs")));
        _menu.Items.Add(new ToolStripSeparator());

        if (allHealthy)
            _menu.Items.Add(new ToolStripMenuItem(
                "Status: All services healthy", null, null, "status"));
        else
            _menu.Items.Add(new ToolStripMenuItem(
                $"Status: {string.Join(", ", unhealthy!)} unhealthy",
                null, null, "status"));

        _menu.Items.Add(new ToolStripSeparator());
        _menu.Items.Add(new ToolStripMenuItem("Restart Backend", null,
            (_, _) => OnMenuClick?.Invoke("restart-backend")));
        _menu.Items.Add(new ToolStripMenuItem("Restart Frontend", null,
            (_, _) => OnMenuClick?.Invoke("restart-frontend")));
        _menu.Items.Add(new ToolStripSeparator());
        _menu.Items.Add(new ToolStripMenuItem("View Logs", null,
            (_, _) => OpenUrl("file:///C:/Users/SLuh/AppData/Local/Temp/opencode/bg-out.log")));
        _menu.Items.Add(new ToolStripMenuItem("Exit", null,
            (_, _) => Application.Exit()));
    }

    public void UpdateIcon(bool allHealthy)
    {
        var color = allHealthy ? Color.LimeGreen : Color.Orange;
        var newIcon = CreateIcon(color);
        _currentIcon?.Dispose();
        _currentIcon = newIcon;
        _tray.Icon = newIcon;
    }

    public void UpdateTooltip(ServiceInfo backend, ServiceInfo frontend, ServiceInfo llm)
    {
        var b = backend.Healthy ? "\u2713" : "\u2717"; // ✓ or ✗
        var f = frontend.Healthy ? "\u2713" : "\u2717";
        var l = llm.Healthy ? "\u2713" : "\u2717";
        _tray.Text = $"Narrative Engine\nBackend {b} | Frontend {f} | LLM {l}";
    }

    public void ShowBalloonTip(string title, string message, ToolTipIcon icon = ToolTipIcon.Info)
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
        _ = Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
    }

    public void Invoke(Action action) => _marshaler.Invoke(action);
    public void Dispose()
    {
        _currentIcon?.Dispose();
        _tray.Dispose();
    }
}
