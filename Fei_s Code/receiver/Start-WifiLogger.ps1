<#
.SYNOPSIS
    Logs Wi-Fi signal metrics every N seconds during an experiment.

.EXAMPLE
    .\Start-WifiLogger.ps1 -ExperimentName "baseline_b1" -Duration 120 -Interval 5
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName,

    [Parameter(Mandatory=$false)]
    [int]$Duration = 120,

    [Parameter(Mandatory=$false)]
    [int]$Interval = 5
)

$ResultDir = "C:\Users\Fei\Documents\Programs\cs578\receiver\results\$ExperimentName"
$LogFile = "$ResultDir\wifi_signal_log.csv"

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

"Timestamp,ElapsedSeconds,Signal,RxRate,TxRate,Channel" | Out-File $LogFile -Encoding UTF8

$startTime = Get-Date
$elapsed = 0

Write-Host "[WiFi] Logging signal every ${Interval}s for ${Duration}s..."

while ($elapsed -lt $Duration) {
    $raw = netsh wlan show interfaces
    $signal = ($raw | Select-String "Signal\s+:\s+(\d+)%").Matches.Groups[1].Value
    $rxRate = ($raw | Select-String "Receive rate\s+\(Mbps\)\s+:\s+([\d.]+)").Matches.Groups[1].Value
    $txRate = ($raw | Select-String "Transmit rate\s+\(Mbps\)\s+:\s+([\d.]+)").Matches.Groups[1].Value
    $channel = ($raw | Select-String "Channel\s+:\s+(\d+)").Matches.Groups[1].Value

    $timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fff")
    "$timestamp,$([math]::Round($elapsed,1)),$signal,$rxRate,$txRate,$channel" | Out-File $LogFile -Append -Encoding UTF8

    Start-Sleep -Seconds $Interval
    $elapsed = ((Get-Date) - $startTime).TotalSeconds
}

Write-Host "[WiFi] Done. Log: $LogFile"

