# Starts a Cloudflare quick tunnel for the Quorum backend and automatically
# points the GitHub App webhook at the current tunnel URL.
#
# Usage:
#   .\scripts\start-tunnel.ps1            # start tunnel + sync webhook
#   .\scripts\start-tunnel.ps1 -Stop      # stop the running tunnel
#
# After this, webhook delivery stays correct even though quick-tunnel URLs
# change on every restart (the script re-syncs each time it runs).

param(
    [string]$Port = "8000",
    [switch]$Stop
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$log = Join-Path $env:TEMP "quorum_tunnel.log"
$logErr = "$log.err"
$urlPattern = "https://[a-zA-Z0-9-]+\.trycloudflare\.com"

function Find-Cloudflared {
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    if (Test-Path "C:\cloudflared\cloudflared.exe") { return "C:\cloudflared\cloudflared.exe" }
    return $null
}

function Read-TunnelUrl {
    if (-not (Test-Path $log)) { return $null }
    $match = Get-Content $log -ErrorAction SilentlyContinue |
        Select-String -Pattern $urlPattern | Select-Object -First 1
    if ($match) { return $match.Matches[0].Value }
    return $null
}

$cloudflared = Find-Cloudflared
if (-not $cloudflared) {
    Write-Host "cloudflared not found on PATH or at C:\cloudflared\cloudflared.exe" -ForegroundColor Red
    exit 1
}

if ($Stop) {
    Get-Process -Name cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "cloudflared stopped." -ForegroundColor Yellow
    exit 0
}

$existing = Get-Process -Name cloudflared -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "cloudflared is already running - re-reading its tunnel URL..."
    $url = Read-TunnelUrl
    if (-not $url) {
        Write-Host "Running cloudflared was not started by this script; stop it first:" -ForegroundColor Yellow
        Write-Host "  .\scripts\start-tunnel.ps1 -Stop" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "Starting cloudflared quick tunnel -> http://localhost:$Port"
    Remove-Item $log, $logErr -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $cloudflared -ArgumentList "tunnel", "--url", "http://localhost:$Port" `
        -RedirectStandardOutput $log -RedirectStandardError $logErr -PassThru -WindowStyle Hidden

    $url = $null
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        if ($p.HasExited) {
            Write-Host "cloudflared exited early. Last error output:" -ForegroundColor Red
            Get-Content $logErr -ErrorAction SilentlyContinue | Select-Object -Last 10
            exit 1
        }
        $url = Read-TunnelUrl
        if ($url) { break }
    }
    if (-not $url) {
        Write-Host "Timed out waiting for the tunnel URL." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Tunnel URL: $url" -ForegroundColor Cyan
$py = Join-Path $root ".venv\Scripts\python.exe"
& $py (Join-Path $PSScriptRoot "sync_github_webhook.py") --url $url
if ($LASTEXITCODE -ne 0) {
    Write-Host "Webhook sync FAILED - run it manually with the URL above." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Done. Tunnel is running at $url" -ForegroundColor Green
Write-Host "Stop it anytime with:  .\scripts\start-tunnel.ps1 -Stop"