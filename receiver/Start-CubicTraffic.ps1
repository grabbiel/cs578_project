
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

$ResultDir = "C:\rledbat-testbed\results\$ExperimentName"
$LogFile = "$ResultDir\iperf3_client.json"

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

Write-Host "============================================="
Write-Host " iperf3 CUBIC Client — $ExperimentName"
Write-Host " Server: ${ServerIp}:${Port}"
Write-Host " Duration: ${Duration}s"
Write-Host "============================================="

& C:\tools\iperf3\iperf3.exe -c $ServerIp -p $Port `
    -t $Duration `
    -R `
    --json `
    --logfile $LogFile

Write-Host "[iperf3] Complete. Results: $LogFile"
