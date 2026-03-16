<#
.SYNOPSIS
    Starts a BITS transfer using rLEDBAT (Priority Low) and monitors progress.

.PARAMETER ExperimentName
    Name for this experiment run (used for log file naming).

.PARAMETER Duration
    Maximum duration in seconds.

.EXAMPLE
    .\Start-RledbatTransfer.ps1 -ExperimentName "baseline_b1" -Duration 120
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName,

    [Parameter(Mandatory=$false)]
    [int]$Duration = 120,

    [Parameter(Mandatory=$false)]
    [string]$SourceUrl = "http://10.0.1.1:8080/testfile.bin"
)

$ResultDir = "C:\Users\Fei\Documents\Programs\cs578\receiver\results\$ExperimentName"
$DestFile = "C:\temp\testfile_${ExperimentName}.bin"
$LogFile = "$ResultDir\bits_transfer.csv"
$SummaryFile = "$ResultDir\bits_summary.txt"

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

# Clean up previous
Get-BitsTransfer -ErrorAction SilentlyContinue | Remove-BitsTransfer -ErrorAction SilentlyContinue
Remove-Item $DestFile -ErrorAction SilentlyContinue

# Write-Host "============================================="
# Write-Host " BITS Transfer — $ExperimentName"
# Write-Host " Source: $SourceUrl"
# Write-Host " Priority: Low (rLEDBAT)"
# Write-Host " Max Duration: ${Duration}s"
# Write-Host "============================================="

# Initialize CSV
"Timestamp,ElapsedSeconds,BytesTransferred,BytesTotal,PercentComplete,JobState" | Out-File $LogFile -Encoding UTF8

$startTime = Get-Date

$job = Start-BitsTransfer -Source $SourceUrl `
    -Destination $DestFile `
    -Priority Low `
    -Asynchronous `
    -DisplayName "rLEDBAT_${ExperimentName}"

if (-not $job) {
    Write-Host "[BITS] ERROR: Failed to start transfer"
    exit 1
}

# Write-Host "[BITS] Transfer started. Job ID: $($job.JobId)"

$prevBytes = 0
$elapsed = 0

while ($elapsed -lt $Duration) {
    Start-Sleep -Seconds 1
    $elapsed = ((Get-Date) - $startTime).TotalSeconds

    $job = Get-BitsTransfer -JobId $job.JobId -ErrorAction SilentlyContinue
    if (-not $job) {
        Write-Host "[BITS] Transfer job no longer exists"
        break
    }

    $bytesTransferred = $job.BytesTransferred
    $bytesTotal = $job.BytesTotal
    $state = $job.JobState

    $bytesDelta = $bytesTransferred - $prevBytes
    $throughputMbps = [math]::Round(($bytesDelta * 8) / 1000000, 2)
    $prevBytes = $bytesTransferred

    if ($bytesTotal -gt 0) {
        $pct = [math]::Round(($bytesTransferred / $bytesTotal) * 100, 1)
    } else {
        $pct = 0
    }

    $timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fff")
    "$timestamp,$([math]::Round($elapsed,1)),$bytesTransferred,$bytesTotal,$pct,$state" | Out-File $LogFile -Append -Encoding UTF8

    $mbTransferred = [math]::Round($bytesTransferred / 1MB, 1)
    Write-Host ("[BITS] {0:N0}s | {1:N1} MB | {2:N1}% | {3:N2} Mbps | {4}" -f `
        [math]::Floor($elapsed), $mbTransferred, $pct, $throughputMbps, $state)

    if ($state -eq "Transferred") {
        Write-Host "[BITS] Transfer complete!"
        Complete-BitsTransfer -BitsJob $job
        break
    }

    if ($state -eq "Error" -or $state -eq "TransientError") {
        Write-Host "[BITS] Transfer error: $($job.ErrorDescription)"
        break
    }
}

$endTime = Get-Date
$totalElapsed = ($endTime - $startTime).TotalSeconds
$avgThroughputMbps = [math]::Round(($prevBytes * 8) / ($totalElapsed * 1000000), 2)

$summary = @"
Experiment: $ExperimentName
Start Time: $($startTime.ToString('yyyy-MM-ddTHH:mm:ss'))
End Time: $($endTime.ToString('yyyy-MM-ddTHH:mm:ss'))
Duration: $([math]::Round($totalElapsed, 1)) seconds
Bytes Transferred: $prevBytes
MB Transferred: $([math]::Round($prevBytes / 1MB, 1))
Average Throughput: $avgThroughputMbps Mbps
Final State: $(if ($job) { $job.JobState } else { "Unknown" })
"@

$summary | Out-File $SummaryFile -Encoding UTF8
Write-Host $summary

Get-BitsTransfer -ErrorAction SilentlyContinue | Remove-BitsTransfer -ErrorAction SilentlyContinue
Remove-Item $DestFile -ErrorAction SilentlyContinue
