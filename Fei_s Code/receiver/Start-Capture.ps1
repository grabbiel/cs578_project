<#
.SYNOPSIS
    Captures packets on the Wi-Fi interface using tshark.

.EXAMPLE
    .\Start-Capture.ps1 -ExperimentName "baseline_b1" -Duration 130
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ExperimentName,

    [Parameter(Mandatory=$false)]
    [int]$Duration = 130
)

$ResultDir = "C:\Users\Fei\Documents\Programs\cs578\receiver\results\$ExperimentName"
$PcapFile = "$ResultDir\receiver_capture.pcap"
$TsharkPath = "C:\Program Files\Wireshark\tshark.exe"

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null

# Find the Wi-Fi interface number
Write-Host "[Capture] Available interfaces:"
& $TsharkPath -D 2>&1 | Write-Host

# Use the Wi-Fi interface — you may need to adjust this name
$WifiInterface = "Wi-Fi"

Write-Host ""
Write-Host " Packet Capture — $ExperimentName"
Write-Host " Interface: $WifiInterface | Duration: ${Duration}s"
Write-Host ""

# -s 128: capture enough for IP + TCP headers + TCP options (timestamps)
& $TsharkPath -i $WifiInterface `
    -f "host 10.0.1.1 and tcp" `
    -w $PcapFile `
    -s 128 `
    -a duration:$Duration

Write-Host "[Capture] File: $PcapFile ($([math]::Round((Get-Item $PcapFile).Length / 1MB, 1)) MB)"
