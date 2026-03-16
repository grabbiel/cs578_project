<#
.SYNOPSIS
    Extracts RCV.WND and timestamp data from a packet capture.

.DESCRIPTION
    Parses the pcap and extracts:
    1. TCP window size from packets SENT BY Host R — this is rLEDBAT's
       RLWND, the algorithm's primary output.
    2. TCP timestamps from packets RECEIVED BY Host R — these carry the
       sender's TSval used by rLEDBAT for delay estimation.

.EXAMPLE
    .\Extract-WindowSize.ps1 -ExperimentName "attack_a1_50ms"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName
)

$ResultDir = "C:\Users\Fei\Documents\Programs\cs578\receiver\results\$ExperimentName"
$PcapFile = "$ResultDir\receiver_capture.pcap"
$WindowCsv = "$ResultDir\rcv_wnd.csv"
$RttCsv = "$ResultDir\timestamps.csv"
$TsharkPath = "C:\Program Files\Wireshark\tshark.exe"

if (-not (Test-Path $PcapFile)) {
    Write-Host "ERROR: Capture file not found: $PcapFile"
    exit 1
}

# ── RCV.WND from Host R's outbound packets (ACKs) ──
Write-Host "[Extract] RCV.WND from Host R → Host S packets..."

& $TsharkPath -r $PcapFile `
    -Y "ip.src == 10.0.2.100 and tcp" `
    -T fields `
    -e frame.time_relative `
    -e tcp.window_size_value `
    -e tcp.window_size `
    -e tcp.ack `
    -e tcp.options.timestamp.tsval `
    -e tcp.options.timestamp.tsecr `
    -E header=y `
    -E separator="," `
    -E quote=n | Out-File $WindowCsv -Encoding UTF8

$lines1 = (Get-Content $WindowCsv | Measure-Object -Line).Lines - 1
Write-Host "  $lines1 records → $WindowCsv"

# ── Timestamps from Host S's inbound packets ──
Write-Host "[Extract] Timestamps from Host S → Host R packets..."

& $TsharkPath -r $PcapFile `
    -Y "ip.src == 10.0.1.1 and tcp" `
    -T fields `
    -e frame.time_relative `
    -e tcp.seq `
    -e tcp.len `
    -e tcp.options.timestamp.tsval `
    -e tcp.options.timestamp.tsecr `
    -e tcp.window_size_value `
    -E header=y `
    -E separator="," `
    -E quote=n | Out-File $RttCsv -Encoding UTF8

$lines2 = (Get-Content $RttCsv | Measure-Object -Line).Lines - 1
Write-Host "  $lines2 records → $RttCsv"

Write-Host "[Extract] Done."
