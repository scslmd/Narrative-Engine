# Validation script - run all checks in parallel
# Usage: scripts\run_validation.ps1

Write-Host "Running validation checks in parallel..." -ForegroundColor Cyan
Write-Host ""

# Define validation commands
$commands = @(
    @{Name="Backend Tests"; Script={ python -m pytest -q -p no:cacheprovider }},
    @{Name="Frontend Lint"; Script={ cd frontend; npm run lint }},
    @{Name="Frontend Typecheck"; Script={ cd frontend; npm run typecheck }},
    @{Name="Frontend Build"; Script={ cd frontend; npm run build }}
)

# Run all commands in parallel
$jobs = @()
foreach ($cmd in $commands) {
    Write-Host "Starting $($cmd.Name)..." -ForegroundColor Yellow
    $jobs += Start-Job -ScriptBlock $cmd.Script -Name $cmd.Name
}

Write-Host ""
Write-Host "All validation checks started. Waiting for completion..." -ForegroundColor Cyan
Write-Host ""

# Wait for all jobs and display results
$results = @()
foreach ($job in $jobs) {
    $result = Wait-Job -Job $job | Receive-Job
    $results += [PSCustomObject]@{
        Name = $job.Name
        Output = $result -join "`n"
        Status = $job.State
    }
    Remove-Job -Job $job
}

Write-Host "=== Validation Results ===" -ForegroundColor Cyan
foreach ($r in $results) {
    Write-Host ""
    Write-Host "$($r.Name):" -ForegroundColor $(if ($r.Status -eq "Completed") "Green" else "Red")
    Write-Host $r.Output
}

# Check if all passed
$allPassed = ($results | Where-Object { $_.Status -eq "Completed" }).Count -eq $commands.Count
Write-Host ""
if ($allPassed) {
    Write-Host "All validation checks PASSED!" -ForegroundColor Green
} else {
    Write-Host "Some validation checks FAILED!" -ForegroundColor Red
    exit 1
}
