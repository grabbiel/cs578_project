
param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName,

    [Parameter(Mandatory=$false)]
    [int]$Duration = 130
)

$ResultDir = "C:\rledbat-testbed\results\$ExperimentName"
$PcapFile = "$ResultDir\receiver_capture.pcap"
$TsharkPath = "C:\Program Files\Wireshark\tshark.exe"

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

Write-Host "[Capture] Available interfaces:"
& $TsharkPath -D 2>&1 | Write-Host

$WifiInterface = "Wi-Fi"

Write-Host ""
Write-Host " Packet Capture — $ExperimentName"
Write-Host " Interface: $WifiInterface | Duration: ${Duration}s"
Write-Host ""

& $TsharkPath -i $WifiInterface `
    -f "host 10.0.1.1 and tcp" `
    -w $PcapFile `
    -s 128 `
    -a duration:$Duration

Write-Host "[Capture] File: $PcapFile ($([math]::Round((Get-Item $PcapFile).Length / 1MB, 1)) MB)"
