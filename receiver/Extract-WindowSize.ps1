
param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName
)

$ResultDir = "C:\rledbat-testbed\results\$ExperimentName"
$PcapFile = "$ResultDir\receiver_capture.pcap"
$WindowCsv = "$ResultDir\rcv_wnd.csv"
$RttCsv = "$ResultDir\timestamps.csv"
$TsharkPath = "C:\Program Files\Wireshark\tshark.exe"

if (-not (Test-Path $PcapFile)) {
    Write-Host "ERROR: Capture file not found: $PcapFile"
    exit 1
}

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
