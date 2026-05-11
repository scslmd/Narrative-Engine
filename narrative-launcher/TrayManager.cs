using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;

namespace NarrativeLauncher;

public class TrayManager
{
    private readonly Control _marshaler = new();
    private readonly NotifyIcon _tray;
    private readonly ContextMenuStrip _menu;
    private Icon? _currentIcon;
    public Action<string>? OnMenuClick { get; set; }
    private StatusWindow? _statusWindow;

    private static readonly Dictionary<string, Image> MenuIcons = new()
    {
        ["open"] = CreateGlyph("\uE873"),
        ["docs"] = CreateGlyph("\uE774"),
        ["status"] = CreateGlyph("\u2713"),
        ["restart"] = CreateGlyph("\uE76E"),
        ["logs"] = CreateGlyph("\uE9FF"),
        ["exit"] = CreateGlyph("\u2715"),
    };

    public TrayManager(ServiceManager services)
    {
        _menu = new ContextMenuStrip
        {
            ShowImageMargin = true,
            GripStyle = ToolStripGripStyle.Hidden,
            BackColor = Color.FromArgb(30, 30, 30),
            ForeColor = Color.FromArgb(220, 220, 220),
            Renderer = new MenuRenderer(),
        };
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

        _menu.Items.Add(CreateMenuItem("Open Frontend", "open",
            (_, _) => OpenUrl("http://localhost:5173")));
        _menu.Items.Add(CreateMenuItem("Open API Docs", "docs",
            (_, _) => OpenUrl("http://127.0.0.1:8000/docs")));
        _menu.Items.Add(new ToolStripSeparator());

        if (allHealthy)
            _menu.Items.Add(CreateStatusItem("\u2713 All services healthy"));
        else
            _menu.Items.Add(CreateStatusItem($"Status: {string.Join(", ", unhealthy!)} unhealthy"));

        _menu.Items.Add(new ToolStripSeparator());
        _menu.Items.Add(CreateMenuItem("Restart Backend", "restart",
            (_, _) => OnMenuClick?.Invoke("restart-backend")));
        _menu.Items.Add(CreateMenuItem("Restart Frontend", "restart",
            (_, _) => OnMenuClick?.Invoke("restart-frontend")));
        _menu.Items.Add(new ToolStripSeparator());
        _menu.Items.Add(CreateMenuItem("View Logs", "logs",
            (_, _) => OpenUrl("file:///C:/Users/SLuh/AppData/Local/Temp/opencode/bg-out.log")));
        _menu.Items.Add(CreateMenuItem("Exit", "exit",
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
        var b = backend.Healthy ? "\u2713" : "\u2717";
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
        g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;

        using var gradient = new System.Drawing.Drawing2D.PathGradientBrush(
            new[] { new PointF(16, 16) })
        {
            CenterColor = Lighten(color, 0.3f),
            SurroundColors = new[] { Darken(color, 0.2f) },
        };
        g.FillEllipse(gradient, 4, 4, 24, 24);

        using var pen = new Pen(Darken(color, 0.4f), 1);
        g.DrawEllipse(pen, 3.5f, 3.5f, 25, 25);

        using var font = new Font("Segoe UI", 16F, FontStyle.Bold);
        var text = "N";
        var size = g.MeasureString(text, font);
        var x = (32 - size.Width) / 2;
        var y = (32 - size.Height) / 2;

        using var shadowBrush = new SolidBrush(Color.FromArgb(80, 0, 0, 0));
        g.DrawString(text, font, shadowBrush, x + 1, y + 1);

        using var whiteBrush = new SolidBrush(Color.White);
        g.DrawString(text, font, whiteBrush, x, y);

        return Icon.FromHandle(bmp.GetHicon());
    }

    private static byte Clamp(byte v, float delta) => (byte)Math.Min(255f, Math.Max(0f, v + delta));

    private static Color Lighten(Color c, float factor)
        => Color.FromArgb(Clamp(c.R, (255 - c.R) * factor),
                           Clamp(c.G, (255 - c.G) * factor),
                           Clamp(c.B, (255 - c.B) * factor));

    private static byte ClampDown(byte v, float factor) => (byte)(v * factor);

    private static Color Darken(Color c, float factor)
        => Color.FromArgb(ClampDown(c.R, 1f - factor),
                           ClampDown(c.G, 1f - factor),
                           ClampDown(c.B, 1f - factor));

    private static Image CreateGlyph(string text)
    {
        using var bmp = new Bitmap(16, 16);
        using var g = Graphics.FromImage(bmp);
        g.Clear(Color.Transparent);
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        using var font = new Font("Segoe UI Symbol", 12F);
        using var brush = new SolidBrush(Color.FromArgb(180, 180, 180));
        g.DrawString(text, font, brush, 2f, 1f);
        return (Image)bmp.Clone();
    }

    private static ToolStripMenuItem CreateMenuItem(string text, string iconKey, EventHandler onClick)
    {
        var item = new ToolStripMenuItem(text, MenuIcons[iconKey], onClick)
        {
            BackColor = Color.FromArgb(30, 30, 30),
            ForeColor = Color.FromArgb(220, 220, 220),
            Font = new Font("Segoe UI", 10F),
        };
        item.MouseEnter += (s, _) => item.BackColor = Color.FromArgb(50, 50, 50);
        item.MouseLeave += (s, _) => item.BackColor = Color.FromArgb(30, 30, 30);
        return item;
    }

    private static ToolStripMenuItem CreateStatusItem(string text)
    {
        var item = new ToolStripMenuItem(text)
        {
            BackColor = Color.FromArgb(30, 30, 30),
            ForeColor = Color.FromArgb(150, 150, 150),
            Font = new Font("Segoe UI", 9F),
        };
        return item;
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

private class MenuRenderer : ToolStripProfessionalRenderer { }
}
