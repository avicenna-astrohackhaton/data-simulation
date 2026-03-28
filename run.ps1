param(
    [string]$MissionRoot = "data/raw/ESA-Mission1/ESA-Mission1",
    [string]$Channels = "channel_41,channel_42,channel_43,channel_44,channel_45,channel_46,channel_14,channel_21,channel_29,channel_48,channel_47,channel_49,channel_52,channel_51,channel_50,channel_22,channel_31,channel_39,channel_15,channel_23",
    [string]$FlatCsv = "data/processed/mission1_flat.csv",
    [string]$OutputJsonl = "output/simulated_telemetry.jsonl",
    [string]$OutputNoisyJsonl = "output/corrupted_noisy.jsonl",
    [string]$OutputCleanJsonl = "output/original_clean.jsonl",
    [int]$MaxRows = 300000,
    [ValidateSet("outer", "inner")]
    [string]$Join = "outer"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
}
else {
    $pythonExe = "python"
}

Push-Location $repoRoot
try {
    Write-Host "[1/2] ESA ham veri -> flat CSV donusumu basliyor..."
    & $pythonExe "scripts/convert_esa_to_flat_csv.py" `
        --mission-root $MissionRoot `
        --channels $Channels `
        --output-csv $FlatCsv `
        --join $Join `
        --max-rows $MaxRows

    if ($LASTEXITCODE -ne 0) {
        throw "Donusum adimi basarisiz oldu."
    }

    $env:PYTHONPATH = Join-Path $repoRoot "src"

    Write-Host "[2/3] Radyasyon simulasyonu basliyor..."
    & $pythonExe "scripts/run_simulation.py" `
        --input-csv $FlatCsv `
        --channels $Channels `
        --timestamp-col "timestamp" `
        --output-jsonl $OutputJsonl

    if ($LASTEXITCODE -ne 0) {
        throw "Simulasyon adimi basarisiz oldu."
    }

    Write-Host "[3/3] Cikti istenen JSONL formatina donusturuluyor..."
    & $pythonExe "scripts/split_clean_noisy_jsonl.py" `
        --input-jsonl $OutputJsonl `
        --output-noisy-jsonl $OutputNoisyJsonl `
        --output-clean-jsonl $OutputCleanJsonl `
        --channels $Channels

    if ($LASTEXITCODE -ne 0) {
        throw "JSONL ayristirma adimi basarisiz oldu."
    }

    Write-Host "Tamamlandi."
    Write-Host "Ara cikti: $OutputJsonl"
    Write-Host "Kirli final cikti: $OutputNoisyJsonl"
    Write-Host "Temiz final cikti: $OutputCleanJsonl"
}
finally {
    Pop-Location
}
