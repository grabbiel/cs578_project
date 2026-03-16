<#
.SYNOPSIS
    Starts an ETW network trace capturing TCP internals.

.DESCRIPTION
    Uses netsh trace to capture kernel-level TCP events. The .etl file
    can be analyzed with netsh trace convert or Microsoft Message Analyzer.

.EXAMPLE
    .\Start-TcpTrace.ps1 -ExperimentName "baseline_b1" -Duration 130
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName,

    [Parameter(Mandatory=$false)]
    [int]$Duration = 130
)

$ResultDir = "C:\Users\Fei\Documents\Programs\cs578\receiver\results\$ExperimentName"
$TraceFile = "$ResultDir\tcp_trace.etl"

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

Write-Host " ETW TCP Trace — $ExperimentName | Duration: ${Duration}s"

netsh trace start capture=yes `
    scenario=NetConnection `
    level=5 `
    tracefile=$TraceFile `
    maxsize=512 `
    overwrite=yes `
    report=disabled

Start-Sleep -Seconds $Duration

netsh trace stop

Write-Host "[Trace] File: $TraceFile ($([math]::Round((Get-Item $TraceFile).Length / 1MB, 1)) MB)"
Write-Host "[Trace] Convert with: netsh trace convert $TraceFile"

