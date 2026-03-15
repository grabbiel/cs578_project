
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

$ResultDir = "C:\rledbat-testbed\results\$ExperimentName"
$ScriptDir = "C:\rledbat-testbed\scripts"
$CaptureDuration = $Duration + 10

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

Write-Host "============================================="
Write-Host " Host R — Experiment: $ExperimentName"
Write-Host " Duration: ${Duration}s"
Write-Host " CUBIC: $WithCubic | ETW: $(-not $SkipTrace)"
Write-Host " Results: $ResultDir"
Write-Host "============================================="

Write-Host "[1] Cleaning previous state..."
Get-BitsTransfer -ErrorAction SilentlyContinue | Remove-BitsTransfer -ErrorAction SilentlyContinue
Remove-Item "C:\temp\testfile_*.bin" -ErrorAction SilentlyContinue

Write-Host "[2] Recording system info..."
$sysInfo = @"
Experiment: $ExperimentName
Date: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
Duration: ${Duration}s
Windows: $([System.Environment]::OSVersion.VersionString)
Build: $((Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').DisplayVersion)

--- Wi-Fi ---
$(netsh wlan show interfaces)

--- IP ---
$(Get-NetIPAddress -InterfaceAlias "Wi-Fi" -AddressFamily IPv4 | Format-List | Out-String)

--- TCP Global ---
$(netsh interface tcp show global)
"@
$sysInfo | Out-File "$ResultDir\system_info.txt" -Encoding UTF8

Write-Host "[3] Checking connectivity..."
if (-not (Test-Connection -ComputerName 10.0.1.1 -Count 2 -Quiet)) {
    Write-Host "ERROR: Cannot reach Host S (10.0.1.1)"
    exit 1
}
Write-Host "  Host S: OK"

Write-Host "[4] Starting packet capture..."
$captureJob = Start-Job -ScriptBlock {
    param($TsharkPath, $PcapFile, $Dur)
    & $TsharkPath -i "Wi-Fi" -f "host 10.0.1.1 and tcp" -w $PcapFile -s 128 -a "duration:$Dur"
} -ArgumentList "C:\Program Files\Wireshark\tshark.exe", "$ResultDir\receiver_capture.pcap", $CaptureDuration
Start-Sleep -Seconds 2

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

Write-Host "[8] Starting BITS transfer (rLEDBAT)..."
Write-Host ""
& "$ScriptDir\Start-RledbatTransfer.ps1" `
    -ExperimentName $ExperimentName `
    -Duration $Duration `
    -SourceUrl $SourceUrl

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

if (-not $SkipTrace) {
    netsh trace stop | Out-Null
    Write-Host "  ETW trace: done"
}

Write-Host ""
Write-Host "[10] Extracting RCV.WND and timestamps..."
& "$ScriptDir\Extract-WindowSize.ps1" -ExperimentName $ExperimentName

netsh wlan show interfaces | Out-File "$ResultDir\wifi_final.txt" -Encoding UTF8

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
