using System.Diagnostics;

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
