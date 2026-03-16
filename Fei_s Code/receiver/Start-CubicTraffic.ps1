<#
.SYNOPSIS
    Starts iperf3 as a CUBIC TCP client downloading from Host S.

.EXAMPLE
    .\Start-CubicTraffic.ps1 -ExperimentName "baseline_b2" -Duration 120
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName,

    [Parameter(Mandatory=$false)]
    [int]$Duration = 120,

    [Parameter(Mandatory=$false)]
    [string]$ServerIp = "10.0.1.1",

    [Parameter(Mandatory=$false)]
    [int]$Port = 5201
)

$ResultDir = "C:\Users\Fei\Documents\Programs\cs578\receiver\results\$ExperimentName"
$LogFile = "$ResultDir\iperf3_client.json"

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

Write-Host "============================================="
Write-Host " iperf3 CUBIC Client — $ExperimentName"
Write-Host " Server: ${ServerIp}:${Port}"
Write-Host " Duration: ${Duration}s"
Write-Host "============================================="

# -R flag: reverse mode — server sends, client receives
# This makes Host R the receiver for CUBIC traffic too,
# matching the real scenario where Host R downloads from Host S
& C:\tools\iperf3\iperf3.exe -c $ServerIp -p $Port `
    -t $Duration `
    -R `
    --json `
    --logfile $LogFile

Write-Host "[iperf3] Complete. Results: $LogFile"
