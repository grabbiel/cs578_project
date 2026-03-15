
param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName,

    [Parameter(Mandatory=$false)]
    [int]$Duration = 130
)

$ResultDir = "C:\rledbat-testbed\results\$ExperimentName"
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

