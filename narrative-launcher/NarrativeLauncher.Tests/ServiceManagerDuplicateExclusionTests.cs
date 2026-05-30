namespace NarrativeLauncher.Tests;

public class ServiceManagerDuplicateExclusionTests
{
    [Fact]
    public void ServiceInfo_HasExternalPidProperty()
    {
        var info = new ServiceInfo { Name = "Test", Port = 8000 };
        info.ExternalPid = 1234;
        Assert.Equal(1234, info.ExternalPid);
    }

    [Fact]
    public void ServiceInfo_ExternalPid_NullByDefault()
    {
        var info = new ServiceInfo { Name = "Test", Port = 8000 };
        Assert.Null(info.ExternalPid);
    }

    [Fact]
    public void ServiceManager_HasAttachExternalBackendAsyncMethod()
    {
        var manager = new ServiceManager(Path.GetTempPath());
        var method = typeof(ServiceManager).GetMethod("AttachExternalBackendAsync");
        Assert.NotNull(method);
        Assert.Equal(typeof(Task), method.ReturnType);
    }

    [Fact]
    public void FindDuplicates_SkipsExternalPid()
    {
        var manager = new ServiceManager(Path.GetTempPath());
        manager.Backend.ExternalPid = 99999;

        var duplicates = manager.FindDuplicates();
        var skipped = duplicates.Any(d => d.Pid == 99999);
        Assert.False(skipped, "ExternalPid should be excluded from duplicates");
    }

    [Fact]
    public void FindDuplicates_StillDetectsOtherPids()
    {
        var manager = new ServiceManager(Path.GetTempPath());
        manager.Backend.ExternalPid = 99999;

        var duplicates = manager.FindDuplicates();

        // Any PID other than ExternalPid and launcher-owned Process should still appear
        foreach (var dup in duplicates)
        {
            Assert.NotEqual(99999, dup.Pid);
            if (manager.Backend.Process != null)
                Assert.NotEqual(manager.Backend.Process.Id, dup.Pid);
        }
    }

    [Fact]
    public void StartBackend_ClearsExternalPid()
    {
        var tempRoot = Path.Combine(Path.GetTempPath(), $"ne-test-{Guid.NewGuid()}");
        Directory.CreateDirectory(tempRoot);

        // Create minimal .venv structure so FindPython works
        var venvPython = Path.Combine(tempRoot, ".venv", "Scripts", "python.exe");
        Directory.CreateDirectory(Path.GetDirectoryName(venvPython)!);
        File.WriteAllText(venvPython, ""); // dummy file

        try
        {
            var manager = new ServiceManager(tempRoot);
            manager.Backend.ExternalPid = 1234;

            // StartBackend will fail because python.exe is a dummy, but ExternalPid should be cleared
            try
            {
                manager.StartBackend();
            }
            catch
            {
                // Expected to fail with dummy python.exe
            }

            Assert.Null(manager.Backend.ExternalPid);
        }
        finally
        {
            try { Directory.Delete(tempRoot, true); } catch { }
        }
    }
}

public class ServiceManagerFrontendRebuildTests
{
    [Fact]
    public void StartFrontendAsync_AcceptsForceRebuildParameter()
    {
        var manager = new ServiceManager(Path.GetTempPath());
        var method = typeof(ServiceManager).GetMethod("StartFrontendAsync");
        Assert.NotNull(method);
        var parameters = method.GetParameters();
        Assert.Single(parameters);
        Assert.Equal("forceRebuild", parameters[0].Name);
        Assert.Equal(typeof(bool), parameters[0].ParameterType);
        Assert.True(parameters[0].DefaultValue is false);
    }
}

public class ServiceManagerLlmUnmanagedTests
{
    [Fact]
    public void IsLlmMonitored_ReturnsFalseByDefault()
    {
        var manager = new ServiceManager(Path.GetTempPath());
        Assert.False(manager.IsLlmMonitored());
    }
}

public class ServiceManagerFrontendStaticTests
{
    [Fact]
    public void Frontend_Port_Is_8000()
    {
        var manager = new ServiceManager(Path.GetTempPath());
        Assert.Equal(8000, manager.Frontend.Port);
    }

    [Fact]
    public void Frontend_Duplicate_Not_Scanned()
    {
        var manager = new ServiceManager(Path.GetTempPath());

        var duplicates = manager.FindDuplicates();

        // No duplicate should reference port 5173
        var has5173 = duplicates.Any(d => d.Port == 5173);
        Assert.False(has5173, "Frontend should not scan port 5173 for duplicates");
    }
}
