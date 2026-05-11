using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace NarrativeLauncher;

public class StatusWindow : Form
{
    private readonly ServiceManager _services;
    private readonly Label[] _statusLabels = new Label[3];
    private readonly PictureBox[] _statusDots = new PictureBox[3];
    private readonly System.Windows.Forms.Timer _refreshTimer;
    private readonly Stopwatch _uptime = Stopwatch.StartNew();

    // Frontend-aligned dark tokens (slate palette)
    private static readonly Color Base = Color.FromArgb(17, 24, 39);
    private static readonly Color PrimarySurface = Color.FromArgb(31, 41, 55);
    private static readonly Color SecondarySurface = Color.FromArgb(30, 41, 59);
    private static readonly Color Border = Color.FromArgb(55, 65, 81);
    private static readonly Color TextPrimary = Color.FromArgb(249, 250, 251);
    private static readonly Color TextSecondary = Color.FromArgb(148, 163, 184);
    private static readonly Color TextMuted = Color.FromArgb(100, 116, 139);
    private static readonly Color Success = Color.FromArgb(52, 211, 153);
    private static readonly Color Warning = Color.FromArgb(251, 191, 36);
    private static readonly Color Danger = Color.FromArgb(248, 113, 113);
    private static readonly Color Indigo = Color.FromArgb(99, 102, 241);
    private static readonly Color Violet = Color.FromArgb(167, 139, 250);
    private static readonly Color Emerald = Color.FromArgb(52, 211, 153);

    public StatusWindow(ServiceManager services)
    {
        _services = services;

        Text = "Narrative Engine";
        Size = new Size(420, 300);
        MinimumSize = new Size(420, 300);
        MaximumSize = new Size(420, 300);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        MinimizeBox = false;
        BackColor = Base;

        var panel = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 6,
            Padding = new Padding(20),
            ColumnStyles = { new ColumnStyle(SizeType.Percent, 100) },
        };

        // Brand row: icon + title
        var brandPanel = new FlowLayoutPanel
        {
            FlowDirection = FlowDirection.LeftToRight,
            AutoSize = true,
        };

        var brandIcon = CreateBrandBadge();
        brandPanel.Controls.Add(brandIcon);

        var headerLabel = new Label
        {
            Text = "Narrative Engine",
            Font = new Font("Inter", 16F, FontStyle.Bold),
            ForeColor = TextPrimary,
            AutoSize = false,
            Height = 28,
        };
        brandPanel.Controls.Add(headerLabel);

        panel.Controls.Add(brandPanel, 0, 0);

        // Subtitle
        var subtitle = new Label
        {
            Text = "Service Status",
            Font = new Font("Inter", 12F, FontStyle.Regular),
            ForeColor = TextMuted,
            AutoSize = false,
            Height = 16,
        };
        panel.Controls.Add(subtitle, 0, 1);

        // Divider
        var divider = new Panel
        {
            Height = 1,
            BackColor = Border,
            Dock = DockStyle.Fill,
        };
        panel.Controls.Add(divider, 0, 2);

        // Service rows
        var titles = new[] { "Backend", "Frontend", "LLM" };
        var ports = new[] { "8000", "5173", "8080" };
        var icons = new[] { "API", "UI", "AI" };
        var iconColors = new[] { Indigo, Emerald, Violet };

        for (int i = 0; i < 3; i++)
        {
            var rowCard = CreateServiceRow(titles[i], ports[i], icons[i], iconColors[i], i);
            panel.Controls.Add(rowCard, 0, i + 3);
        }

        // Bottom row: uptime + quit button
        var bottomPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.RightToLeft,
        };

        var quitBtn = new Button
        {
            Text = "Quit",
            Font = new Font("Inter", 12F, FontStyle.Bold),
            BackColor = Color.FromArgb(239, 68, 68),
            ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat,
            Width = 80,
            Height = 34,
            Cursor = Cursors.Hand,
        };
        quitBtn.FlatAppearance.BorderSize = 0;
        quitBtn.Click += (_, _) => Application.Exit();
        bottomPanel.Controls.Add(quitBtn);

        panel.Controls.Add(bottomPanel, 0, 5);
        Controls.Add(panel);

        // Refresh timer
        _refreshTimer = new System.Windows.Forms.Timer { Interval = 3000 };
        _refreshTimer.Tick += (s, e) => UpdateStatusInternal();
        _refreshTimer.Start();

        UpdateStatusInternal();
    }

    private PictureBox CreateBrandBadge()
    {
        var pb = new PictureBox
        {
            Size = new Size(28, 28),
            BorderStyle = BorderStyle.None,
            Margin = new Padding(0, 0, 10, 0),
        };

        using var bmp = new Bitmap(28, 28);
        using var g = Graphics.FromImage(bmp);
        g.Clear(Color.Transparent);
        g.SmoothingMode = SmoothingMode.AntiAlias;

        // Rounded rectangle background
        var path = new GraphicsPath();
        path.AddRectangle(new Rectangle(0, 0, 28, 28));
        using var gradient = new LinearGradientBrush(new Rectangle(0, 0, 28, 28), Indigo, Violet, 45f);
        g.FillPath(gradient, CreateRoundedRect(0, 0, 28, 28, 8));

        // "N" letter
        using var font = new Font("Inter", 14F, FontStyle.Bold);
        using var brush = new SolidBrush(Color.White);
        var size = g.MeasureString("N", font);
        g.DrawString("N", font, brush, (28 - size.Width) / 2, (28 - size.Height) / 2);

        pb.Image = bmp;
        return pb;
    }

    private Control CreateServiceRow(string name, string port, string iconText, Color iconColor, int index)
    {
        var row = new FlowLayoutPanel
        {
            FlowDirection = FlowDirection.LeftToRight,
            Dock = DockStyle.Fill,
            Margin = new Padding(0, 0, 0, 6),
            BackColor = SecondarySurface,
            Padding = new Padding(12, 10, 12, 10),
        };

        // Left section: service icon + name
        var leftPanel = new FlowLayoutPanel
        {
            FlowDirection = FlowDirection.LeftToRight,
            AutoSize = true,
        };

        var svcIcon = CreateServiceIcon(iconText, iconColor);
        leftPanel.Controls.Add(svcIcon);

        var nameLabel = new Label
        {
            Text = name,
            Font = new Font("Inter", 13F, FontStyle.Regular),
            ForeColor = TextPrimary,
            AutoSize = false,
            Height = 24,
        };
        leftPanel.Controls.Add(nameLabel);

        row.Controls.Add(leftPanel);

        // Spacer (flex)
        var spacer = new Panel
        {
            Dock = DockStyle.Fill,
        };
        row.Controls.Add(spacer);

        // Port pill
        var portPill = new Label
        {
            Text = port,
            Font = new Font("Cascadia Code", 11F, FontStyle.Regular),
            ForeColor = TextMuted,
            BackColor = Color.FromArgb(100, 116, 139),
            AutoSize = false,
            Width = 52,
            Height = 22,
            TextAlign = ContentAlignment.MiddleCenter,
        };
        portPill.BackColor = Color.FromArgb(30, 41, 59);
        portPill.ForeColor = TextMuted;
        row.Controls.Add(portPill);

        // Right section: dot + status text
        var rightPanel = new FlowLayoutPanel
        {
            FlowDirection = FlowDirection.LeftToRight,
            AutoSize = true,
            Margin = new Padding(16, 0, 0, 0),
        };

        var dot = new PictureBox
        {
            Size = new Size(8, 8),
            BorderStyle = BorderStyle.None,
            Margin = new Padding(0, 4, 8, 4),
        };
        _statusDots[index] = dot;
        rightPanel.Controls.Add(dot);

        var statusLbl = new Label
        {
            AutoSize = true,
            Font = new Font("Inter", 12F, FontStyle.Regular),
            ForeColor = TextSecondary,
        };
        _statusLabels[index] = statusLbl;
        rightPanel.Controls.Add(statusLbl);

        row.Controls.Add(rightPanel);

        return row;
    }

    private PictureBox CreateServiceIcon(string text, Color color)
    {
        var pb = new PictureBox
        {
            Size = new Size(24, 24),
            BorderStyle = BorderStyle.None,
            Margin = new Padding(0, 0, 8, 0),
        };

        using var bmp = new Bitmap(24, 24);
        using var g = Graphics.FromImage(bmp);
        g.Clear(Color.Transparent);
        g.SmoothingMode = SmoothingMode.AntiAlias;

        // Background with color tint
        var bg = Color.FromArgb(color.R, color.G, color.B);
        bg = Color.FromArgb(25, bg.R, bg.G, bg.B);
        using var brush = new SolidBrush(bg);
        g.FillRectangle(brush, 0, 0, 24, 24);

        // Text
        using var font = new Font("Inter", 10F, FontStyle.Bold);
        using var textBrush = new SolidBrush(color);
        var size = g.MeasureString(text, font);
        g.DrawString(text, font, textBrush, (24 - size.Width) / 2, (24 - size.Height) / 2);

        pb.Image = bmp;
        return pb;
    }

    public new void Refresh() => UpdateStatusInternal();

    private void UpdateStatusInternal()
    {
        var servicesArr = new ServiceInfo[] { _services.Backend, _services.Frontend, _services.Llm };
        for (int i = 0; i < 3; i++)
        {
            var svc = servicesArr[i];
            var lbl = _statusLabels[i];
            var dot = _statusDots[i];

            if (svc.Healthy)
            {
                lbl.Text = "Running";
                lbl.ForeColor = Success;
                UpdateDot(dot, Success);
            }
            else
            {
                if (svc.Process is { HasExited: false })
                {
                    lbl.Text = "Starting...";
                    lbl.ForeColor = Warning;
                    UpdateDot(dot, Warning);
                }
                else
                {
                    lbl.Text = "Stopped";
                    lbl.ForeColor = Danger;
                    UpdateDot(dot, Danger);
                }
            }
        }
    }

    private static void UpdateDot(PictureBox dot, Color color)
    {
        using var bmp = new Bitmap(8, 8);
        using var g = Graphics.FromImage(bmp);
        g.Clear(Color.Transparent);
        g.SmoothingMode = SmoothingMode.AntiAlias;
        using var brush = new SolidBrush(color);
        g.FillEllipse(brush, 1, 1, 6, 6);

        // Glow effect
        using var glow = new SolidBrush(Color.FromArgb(40, color.R, color.G, color.B));
        g.FillEllipse(glow, -1, -1, 10, 10);

        dot.Image?.Dispose();
        dot.Image = bmp;
    }

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        e.Cancel = true;
        Hide();
    }

    protected override void OnKeyDown(KeyEventArgs e)
    {
        if (e.KeyCode == Keys.Escape)
            Hide();
    }

    private static GraphicsPath CreateRoundedRect(int x, int y, int w, int h, int radius)
    {
        var path = new GraphicsPath();
        path.AddArc(x, y, radius * 2, radius * 2, 90, 90);
        path.AddArc(w - radius * 2, y, radius * 2, radius * 2, 180, 90);
        path.AddArc(w - radius * 2, h - radius * 2, radius * 2, radius * 2, 270, 90);
        path.AddArc(x, h - radius * 2, radius * 2, radius * 2, 0, 90);
        path.CloseFigure();
        return path;
    }
}
