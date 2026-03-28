param(
    [string]$MissionRoot = "data/raw/ESA-Mission1/ESA-Mission1",
    [string]$Channels = "channel_12,channel_13,channel_70,channel_71",
    [string]$FlatCsv = "data/processed/mission1_flat.csv",
    [string]$OutputJsonl = "output/simulated_telemetry.jsonl",
    [int]$MaxRows = 300000,
    [ValidateSet("outer", "inner")]
    [string]$Join = "outer"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
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

    Write-Host "[2/2] Radyasyon simulasyonu basliyor..."
    & $pythonExe "scripts/run_simulation.py" `
        --input-csv $FlatCsv `
        --channels $Channels `
        --timestamp-col "timestamp" `
        --output-jsonl $OutputJsonl

    if ($LASTEXITCODE -ne 0) {
        throw "Simulasyon adimi basarisiz oldu."
    }

    Write-Host "Tamamlandi. Cikti dosyasi: $OutputJsonl"
}
finally {
    Pop-Location
}
