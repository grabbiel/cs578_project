<#
.SYNOPSIS
    Master experiment orchestrator for Host R.

.DESCRIPTION
    Runs a complete experiment: starts packet capture, ETW trace, Wi-Fi
    signal logger, BITS transfer (rLEDBAT), and optionally iperf3 CUBIC.

.PARAMETER ExperimentName
    Name for this experiment run.

.PARAMETER Duration
    Experiment duration in seconds.

.PARAMETER WithCubic
    Also start an iperf3 CUBIC flow alongside the BITS transfer.

.PARAMETER SkipTrace
    Skip the ETW trace (faster startup, less data).

.EXAMPLE
    .\Run-Experiment.ps1 -ExperimentName "baseline_b1" -Duration 120
    .\Run-Experiment.ps1 -ExperimentName "baseline_b2" -Duration 120 -WithCubic
    .\Run-Experiment.ps1 -ExperimentName "attack_a1_50ms" -Duration 120
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName,

    [Parameter(Mandatory=$false)]
    [int]$Duration = 120,

    [Parameter(Mandatory=$false)]
    [switch]$WithCubic,

    [Parameter(Mandatory=$false)]
    [switch]$SkipTrace,

    [Parameter(Mandatory=$false)]
    [string]$SourceUrl = "http://10.0.1.1:8080/testfile.bin",

    [Parameter(Mandatory=$false)]
    [string]$IperfServer = "10.0.1.1",

    [Parameter(Mandatory=$false)]
    [int]$IperfPort = 5201
)

$ResultDir = "C:\Users\Fei\Documents\Programs\cs578\receiver\results\$ExperimentName"
$ScriptDir = "C:\Users\Fei\Documents\Programs\cs578\receiver"
$CaptureDuration = $Duration + 10

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

# Write-Host "============================================="
# Write-Host " Host R — Experiment: $ExperimentName"
# Write-Host " Duration: ${Duration}s"
# Write-Host " CUBIC: $WithCubic | ETW: $(-not $SkipTrace)"
# Write-Host " Results: $ResultDir"
# Write-Host "============================================="

# ── Step 1: Clean up ──
Write-Host "[1] Cleaning previous state..."
Get-BitsTransfer -ErrorAction SilentlyContinue | Remove-BitsTransfer -ErrorAction SilentlyContinue
Remove-Item "C:\temp\testfile_*.bin" -ErrorAction SilentlyContinue

# ── Step 2: System info ──
Write-Host "[2] Recording system info..."
$sysInfo = "sysInfo"
# $sysInfo = @"
# Experiment: $ExperimentName
# Date: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
# Duration: ${Duration}s
# Windows: $([System.Environment]::OSVersion.VersionString)
# Build: $((Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').DisplayVersion)

# --- Wi-Fi ---
$(netsh wlan show interfaces)

# --- IP ---
$(Get-NetIPAddress -InterfaceAlias "Wi-Fi" -AddressFamily IPv4 | Format-List | Out-String)

# --- TCP Global ---
$(netsh interface tcp show global)
# "@
$sysInfo | Out-File "$ResultDir\system_info.txt" -Encoding UTF8

# ── Step 3: Connectivity check ──
Write-Host "[3] Checking connectivity..."
if (-not (Test-Connection -ComputerName 10.0.1.1 -Count 2 -Quiet)) {
    Write-Host "ERROR: Cannot reach Host S (10.0.1.1)"
    exit 1
}
Write-Host "  Host S: OK"

# ── Step 4: Packet capture (background) ──
Write-Host "[4] Starting packet capture..."
$captureJob = Start-Job -ScriptBlock {
    param($TsharkPath, $PcapFile, $Dur)
    & $TsharkPath -i "Wi-Fi" -f "host 10.0.1.1 and tcp" -w $PcapFile -s 128 -a "duration:$Dur"
} -ArgumentList "C:\Program Files\Wireshark\tshark.exe", "$ResultDir\receiver_capture.pcap", $CaptureDuration
Start-Sleep -Seconds 2

# ── Step 5: ETW trace (background, optional) ──
$traceJob = $null
if (-not $SkipTrace) {
    Write-Host "[5] Starting ETW trace..."
    # ETW trace must run in-process (netsh requires elevation context)
    # We start it here and stop it at the end
    netsh trace start capture=yes scenario=NetConnection level=5 `
        tracefile="$ResultDir\tcp_trace.etl" maxsize=512 overwrite=yes report=disabled | Out-Null
} else {
    Write-Host "[5] ETW trace skipped"
}

# ── Step 6: Wi-Fi signal logger (background) ──
Write-Host "[6] Starting Wi-Fi signal logger..."
$wifiJob = Start-Job -ScriptBlock {
    param($LogFile, $Dur)
    "Timestamp,ElapsedSeconds,Signal,RxRate,TxRate,Channel" | Out-File $LogFile -Encoding UTF8
    $start = Get-Date
    while (((Get-Date) - $start).TotalSeconds -lt $Dur) {
        $raw = netsh wlan show interfaces
        $sig = ($raw | Select-String "Signal\s+:\s+(\d+)%").Matches.Groups[1].Value
        $rx = ($raw | Select-String "Receive rate\s+\(Mbps\)\s+:\s+([\d.]+)").Matches.Groups[1].Value
        $tx = ($raw | Select-String "Transmit rate\s+\(Mbps\)\s+:\s+([\d.]+)").Matches.Groups[1].Value
        $ch = ($raw | Select-String "Channel\s+:\s+(\d+)").Matches.Groups[1].Value
        $el = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
        "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.fff'),$el,$sig,$rx,$tx,$ch" | Out-File $LogFile -Append -Encoding UTF8
        Start-Sleep -Seconds 5
    }
} -ArgumentList "$ResultDir\wifi_signal_log.csv", $CaptureDuration

# ── Step 7: iperf3 CUBIC (background, if requested) ──
$iperfJob = $null
if ($WithCubic) {
    Write-Host "[7] Starting iperf3 CUBIC flow..."
    $iperfJob = Start-Job -ScriptBlock {
        param($server, $port, $dur, $logFile)
        & C:\tools\iperf3\iperf3.exe -c $server -p $port -t $dur -R --json --logfile $logFile
    } -ArgumentList $IperfServer, $IperfPort, $Duration, "$ResultDir\iperf3_client.json"
    Start-Sleep -Seconds 1
} else {
    Write-Host "[7] No CUBIC traffic"
}

# ── Step 8: BITS transfer (foreground) ──
Write-Host "[8] Starting BITS transfer (rLEDBAT)..."
Write-Host ""
& "$ScriptDir\Start-RledbatTransfer.ps1" `
    -ExperimentName $ExperimentName `
    -Duration $Duration `
    -SourceUrl $SourceUrl

# ── Step 9: Wait for background jobs ──
Write-Host ""
Write-Host "[9] Waiting for background tasks..."

if ($iperfJob) {
    Wait-Job $iperfJob -Timeout ($Duration + 15) | Out-Null
    Write-Host "  iperf3: done"
}

Wait-Job $captureJob -Timeout ($CaptureDuration + 15) | Out-Null
Write-Host "  Capture: done"

Wait-Job $wifiJob -Timeout ($CaptureDuration + 15) | Out-Null
Write-Host "  Wi-Fi logger: done"

# Stop ETW trace
if (-not $SkipTrace) {
    netsh trace stop | Out-Null
    Write-Host "  ETW trace: done"
}

# ── Step 10: Extract metrics ──
Write-Host ""
Write-Host "[10] Extracting RCV.WND and timestamps..."
& "$ScriptDir\Extract-WindowSize.ps1" -ExperimentName $ExperimentName

# ── Step 11: Final Wi-Fi snapshot ──
netsh wlan show interfaces | Out-File "$ResultDir\wifi_final.txt" -Encoding UTF8

# ── Summary ──
Write-Host ""
Write-Host "============================================="
Write-Host " Experiment complete: $ExperimentName"
Write-Host " Results: $ResultDir"
Write-Host "============================================="
Get-ChildItem $ResultDir | Format-Table Name, @{L="Size";E={
    if ($_.Length -gt 1MB) { "{0:N1} MB" -f ($_.Length / 1MB) }
    else { "{0:N0} KB" -f ($_.Length / 1KB) }
}} -AutoSize

Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue

Set execution policy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
