param([string]$OutputDir = "..")

$ErrorActionPreference = "Stop"
Set-Location $PSScriptPath

Write-Host "Building narrative-launcher..."
dotnet publish -c Release -o "$OutputDir\narrative-launcher" --self-contained false

if ($LASTEXITCODE -eq 0) {
    Write-Host "Built: $OutputDir\narrative-launcher\narrative-launcher.exe"
} else {
    Write-Host "Build failed!"
    exit 1
}
