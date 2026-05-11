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

    // Design tokens (Raycast/Linear-inspired dark surface ladder)
    private static readonly Color Canvas = Color.FromArgb(7, 8, 10);
    private static readonly Color Surface = Color.FromArgb(13, 13, 13);
    private static readonly Color SurfaceElevated = Color.FromArgb(16, 17, 17);
    private static readonly Color Hairline = Color.FromArgb(35, 37, 42);
    private static readonly Color Ink = Color.FromArgb(244, 244, 246);
    private static readonly Color Body = Color.FromArgb(205, 205, 205);
    private static readonly Color Mute = Color.FromArgb(156, 156, 157);
    private static readonly Color Success = Color.FromArgb(89, 212, 153);
    private static readonly Color Warning = Color.FromArgb(255, 197, 51);
    private static readonly Color Error = Color.FromArgb(255, 97, 97);
    private static readonly Color Primary = Color.White;

    public StatusWindow(ServiceManager services)
    {
        _services = services;

        Text = "Narrative Engine";
        Size = new Size(400, 260);
        MinimumSize = new Size(400, 260);
        MaximumSize = new Size(400, 260);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        MinimizeBox = false;
        BackColor = Canvas;

        var panel = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 3,
            RowCount = 7,
            Padding = new Padding(16),
            ColumnStyles =
            {
                new ColumnStyle(SizeType.Percent, 50),  // Service name
                new ColumnStyle(SizeType.Percent, 25),  // Port
                new ColumnStyle(SizeType.Percent, 25),  // Status
            },
        };

        // Header row with title and version
        var headerLabel = new Label
        {
            Text = "Narrative Engine",
            Font = new Font("Segoe UI Variable", 14F, FontStyle.Bold),
            ForeColor = Ink,
            AutoSize = false,
            Dock = DockStyle.Fill,
        };
        panel.Controls.Add(headerLabel, 0, 0);
        panel.SetColumnSpan(headerLabel, 3);

        // Subtitle
        var subtitle = new Label
        {
            Text = "Service Status",
            Font = new Font("Segoe UI Variable", 11F, FontStyle.Regular),
            ForeColor = Mute,
            AutoSize = false,
            Dock = DockStyle.Fill,
        };
        panel.Controls.Add(subtitle, 0, 1);
        panel.SetColumnSpan(subtitle, 3);

        // Hairline divider
        var divider = new Panel
        {
            Height = 1,
            BackColor = Hairline,
            Dock = DockStyle.Fill,
        };
        panel.Controls.Add(divider, 0, 2);
        panel.SetColumnSpan(divider, 3);

        var titles = new[] { "Backend", "Frontend", "LLM" };
        var ports = new[] { "8000", "5173", "8080" };

        // Service rows
        for (int i = 0; i < 3; i++)
        {
            // Service name label (column 0)
            var nameLbl = new Label
            {
                Text = titles[i],
                Font = new Font("Segoe UI Variable", 12F, FontStyle.Regular),
                ForeColor = Body,
                AutoSize = false,
                Dock = DockStyle.Fill,
            };
            panel.Controls.Add(nameLbl, 0, i + 3);

            // Port label (column 1)
            var portLabel = new Label
            {
                Text = ports[i],
                Font = new Font("Cascadia Code", 10F, FontStyle.Regular),
                ForeColor = Mute,
                AutoSize = false,
                Dock = DockStyle.Fill,
            };
            panel.Controls.Add(portLabel, 1, i + 3);

            // Status section (column 2): dot + status text in a flow panel
            var statusPanel = new FlowLayoutPanel
            {
                FlowDirection = FlowDirection.LeftToRight,
                AutoSize = true,
                Dock = DockStyle.None,
            };

            // Status dot
            var dot = new PictureBox
            {
                Size = new Size(8, 8),
                BackColor = SurfaceElevated,
                BorderStyle = BorderStyle.None,
                Margin = new Padding(0, 4, 6, 4),
            };
            _statusDots[i] = dot;
            statusPanel.Controls.Add(dot);

            // Status text
            var statusLbl = new Label
            {
                AutoSize = true,
                Font = new Font("Segoe UI Variable", 11F, FontStyle.Regular),
                ForeColor = Body,
            };
            _statusLabels[i] = statusLbl;
            statusPanel.Controls.Add(statusLbl);

            panel.Controls.Add(statusPanel, 2, i + 3);
        }

        // Spacer row
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 12));

        // Quit button row (span all columns, right-aligned)
        var quitPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.RightToLeft,
        };
        var quitBtn = new Button
        {
            Text = "Quit",
            Font = new Font("Segoe UI Variable", 11F, FontStyle.Bold),
            BackColor = SurfaceElevated,
            ForeColor = Ink,
            FlatStyle = FlatStyle.Flat,
            Width = 80,
            Height = 32,
            Cursor = Cursors.Hand,
        };
        quitBtn.FlatAppearance.BorderSize = 1;
        quitBtn.FlatAppearance.BorderColor = Hairline;
        quitBtn.Click += (_, _) => Application.Exit();
        quitPanel.Controls.Add(quitBtn);
        panel.Controls.Add(quitPanel, 0, 6);
        panel.SetColumnSpan(quitPanel, 3);

        Controls.Add(panel);

        // Refresh timer
        _refreshTimer = new System.Windows.Forms.Timer { Interval = 3000 };
        _refreshTimer.Tick += (s, e) => UpdateStatusInternal();
        _refreshTimer.Start();

        UpdateStatusInternal();
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
                    lbl.ForeColor = Error;
                    UpdateDot(dot, Error);
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
}
