@echo off
REM Binary veri karşılaştırma aracını çalıştırır

echo Binary Veri Karsilastirma Araci
echo ================================
echo.

REM Virtual environment'i aktifleştir
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo UYARI: Virtual environment bulunamadi. Global Python kullaniliyor...
)

REM Python scriptini çalıştır
python scripts\compare_binary_data.py --input-jsonl output\simulated_telemetry.jsonl --max-samples 5 --precision 32bit

pause
