using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
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

    public void SetStatusWindow(StatusWindow window)
    {
        _statusWindow = window;
    }
    private static readonly Color Indigo = Color.FromArgb(99, 102, 241);
    private static readonly Color Violet = Color.FromArgb(167, 139, 250);
    private static readonly Color Amber = Color.FromArgb(245, 158, 11);
    private static readonly Color AmberDark = Color.FromArgb(217, 119, 6);
    private static readonly Color MenuBg = Color.FromArgb(30, 41, 59);
    private static readonly Color MenuHover = Color.FromArgb(38, 53, 69);
    private static readonly Color MenuText = Color.FromArgb(220, 220, 220);
    private static readonly Color MenuMuted = Color.FromArgb(156, 163, 175);

    private static readonly Dictionary<string, Image> MenuIcons = new()
    {
        ["open"] = CreateGlyph("\uE873", Indigo),
        ["docs"] = CreateGlyph("\uE774", Indigo),
        ["status"] = CreateGlyph("\u2713", Color.FromArgb(52, 211, 153)),
        ["restart"] = CreateGlyph("\uE76E", Violet),
        ["logs"] = CreateGlyph("\uE9FF", Color.FromArgb(100, 116, 139)),
        ["exit"] = CreateGlyph("\u2715", Color.FromArgb(248, 113, 113)),
    };

    public TrayManager(ServiceManager services)
    {
        _menu = new ContextMenuStrip
        {
            ShowImageMargin = true,
            GripStyle = ToolStripGripStyle.Hidden,
            BackColor = MenuBg,
            ForeColor = MenuText,
            Renderer = new MenuRenderer(),
        };
        PopulateMenu(true);

        _tray = new NotifyIcon
        {
            Icon = CreateIcon(Indigo, Violet),
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
        _statusWindow.Refresh();
        _statusWindow.Show();
        _statusWindow.BringToFront();
    }

    public void PopulateMenu(bool allHealthy, string[]? unhealthy = null)
    {
        _menu.Items.Clear();

        _menu.Items.Add(CreateMenuItem("Open Frontend", "open",
            (_, _) => OpenUrl("http://127.0.0.1:8000")));
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
            (_, _) => OnMenuClick?.Invoke("exit")));
    }

    public void UpdateIcon(bool allHealthy)
    {
        Icon newIcon;
        if (allHealthy)
            newIcon = CreateIcon(Indigo, Violet);
        else
            newIcon = CreateIcon(Amber, AmberDark);
        _currentIcon?.Dispose();
        _currentIcon = newIcon;
        _tray.Icon = newIcon;
    }

    public void UpdateTooltip(ServiceInfo backend, ServiceInfo frontend, bool llmMonitored, ServiceInfo llm)
    {
        var b = backend.Healthy ? "\u2713" : "\u2717";
        var f = frontend.Healthy ? "\u2713" : "\u2717";
        var llmLine = llmMonitored
            ? $"LLM {(llm.Healthy ? "\u2713" : "\u2717")}"
            : "LLM -";
        _tray.Text = $"Narrative Engine\nBackend {b} | Frontend {f} | {llmLine}\nDouble-click for status";
    }

    public void ShowBalloonTip(string title, string message, ToolTipIcon icon = ToolTipIcon.Info)
    {
        _tray.BalloonTipText = message;
        _tray.BalloonTipTitle = title;
        _tray.ShowBalloonTip(5000);
    }

    private static Icon CreateIcon(Color primary, Color secondary)
    {
        using var bmp = new Bitmap(32, 32);
        using var g = Graphics.FromImage(bmp);
        g.Clear(Color.Transparent);
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;

        // Gradient fill
        using var gradient = new LinearGradientBrush(
            new Rectangle(4, 4, 24, 24), primary, secondary, 135f);
        g.FillEllipse(gradient, 4, 4, 24, 24);

        // Glow shadow
        using var glow = new SolidBrush(Color.FromArgb(60, primary.R, primary.G, primary.B));
        g.FillEllipse(glow, 2, 2, 28, 28);

        // Outer ring
        using var pen = new Pen(Darken(primary, 0.3f), 1.5f);
        g.DrawEllipse(pen, 3.5f, 3.5f, 25, 25);

        // "N" letter with shadow
        using var font = new Font("Inter", 16F, FontStyle.Bold);
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

    private static Color Darken(Color c, float factor)
        => Color.FromArgb((byte)(c.R * (1f - factor)),
                           (byte)(c.G * (1f - factor)),
                           (byte)(c.B * (1f - factor)));

    private static Image CreateGlyph(string text, Color color)
    {
        using var bmp = new Bitmap(16, 16);
        using var g = Graphics.FromImage(bmp);
        g.Clear(Color.Transparent);
        g.SmoothingMode = SmoothingMode.AntiAlias;
        using var font = new Font("Segoe UI Symbol", 12F);
        using var brush = new SolidBrush(color);
        g.DrawString(text, font, brush, 2f, 1f);
        return (Image)bmp.Clone();
    }

    private static ToolStripMenuItem CreateMenuItem(string text, string iconKey, EventHandler onClick)
    {
        var item = new ToolStripMenuItem(text, MenuIcons[iconKey], onClick)
        {
            BackColor = MenuBg,
            ForeColor = MenuText,
            Font = new Font("Inter", 10F),
        };
        item.MouseEnter += (s, _) => item.BackColor = MenuHover;
        item.MouseLeave += (s, _) => item.BackColor = MenuBg;
        return item;
    }

    private static ToolStripMenuItem CreateStatusItem(string text)
    {
        var item = new ToolStripMenuItem(text)
        {
            BackColor = Color.FromArgb(20, 52, 211, 153),
            ForeColor = Color.FromArgb(52, 211, 153),
            Font = new Font("Inter", 9F),
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
