using System.Drawing;
using System.Windows.Forms;

namespace NarrativeLauncher;

public class StatusWindow : Form
{
    private readonly ServiceManager _services;
    private readonly Label[] _statusLabels = new Label[3];
    private readonly System.Windows.Forms.Timer _refreshTimer;

    public StatusWindow(ServiceManager services)
    {
        _services = services;

        Text = "Narrative Engine";
        Size = new Size(380, 220);
        MinimumSize = new Size(380, 220);
        MaximumSize = new Size(380, 220);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        MinimizeBox = false;
        BackColor = Color.White;

        var panel = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 2,
            RowCount = 6,
            Padding = new Padding(16),
            ColumnStyles =
            {
                new ColumnStyle(SizeType.AutoSize),
                new ColumnStyle(),
            },
        };

        var titles = new[] { "Backend (8000)", "Frontend (5173)", "LLM (8080)" };

        // Header row
        var headerLabel = new Label
        {
            Text = "Service Status",
            Font = new Font("Segoe UI", 14F, FontStyle.Bold),
            AutoSize = false,
        };
        panel.Controls.Add(headerLabel, 0, 0);
        panel.SetColumnSpan(headerLabel, 2);

        // Service rows
        for (int i = 0; i < 3; i++)
        {
            var lbl = new Label
            {
                Text = $"{titles[i]}: ",
                Font = new Font("Segoe UI", 10F),
                AutoSize = false,
                Width = 180,
            };
            panel.Controls.Add(lbl, 0, i + 1);

            var statusLbl = new Label
            {
                AutoSize = true,
                Font = new Font("Segoe UI", 10F),
            };
            _statusLabels[i] = statusLbl;
            panel.Controls.Add(statusLbl, 1, i + 1);
        }

        // Spacer row
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 8));

        // Quit button row
        var quitBtn = new Button
        {
            Text = "Quit",
            Font = new Font("Segoe UI", 10F),
            BackColor = Color.FromArgb(240, 240, 240),
            ForeColor = Color.Black,
            FlatStyle = FlatStyle.Flat,
            Width = 80,
            Height = 32,
        };
        quitBtn.Click += (_, _) => Application.Exit();
        panel.Controls.Add(quitBtn, 1, 5);

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
            if (svc.Healthy)
            {
                lbl.Text = "\u2713 Running";
                lbl.ForeColor = Color.LimeGreen;
            }
            else
            {
                lbl.Text = svc.Process is { HasExited: false } ? "\u23F3 Starting..." : "\u2717 Stopped";
                lbl.ForeColor = svc.Process is { HasExited: false } ? Color.Orange : Color.Red;
            }
        }
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
