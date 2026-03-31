# Data Simulation MVP

Bu repo, ESA Mission telemetri verisini işleyip radyasyon etkisi simüle edilmiş çıktı üretir.

## Amaç

Akış üç adımdan oluşur:
1. ESA ham verisini düz (flat) CSV formuna dönüştürme
2. Dinamik radyasyon event simülasyonu üretme
3. Son çıktıyı iki ayrı JSONL dosyasına ayırma

## Üretilen Dosyalar

Varsayılan çalıştırmada aşağıdaki dosyalar üretilir:
- `output/simulated_telemetry.jsonl` (ara çıktı: clean + noisy birlikte)
- `output/corrupted_noisy.jsonl` (final kirli/noisy çıktı)
- `output/original_clean.jsonl` (final temiz/clean çıktı)

Not: Final kullanım için ana dosyalar `corrupted_noisy.jsonl` ve `original_clean.jsonl` dosyalarıdır.

## Kurulum

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Hızlı Çalıştırma

PowerShell:

```powershell
.\run.ps1
```

CMD veya PowerShell (wrapper):

```bat
run.bat
```

Mission 1 için 1000 satırlık örnek çalışma:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run.ps1 -MaxRows 1000 -FlatCsv "data/processed/mission1_1000.csv"
```

## Parametreli Çalıştırma Örneği

```powershell
.\run.ps1 `
  -MissionRoot "data/raw/ESA-Mission1/ESA-Mission1" `
  -Channels "channel_41,channel_42,channel_43,channel_44" `
  -FlatCsv "data/processed/mission1_custom.csv" `
  -OutputJsonl "output/simulated_telemetry.jsonl" `
  -OutputNoisyJsonl "output/corrupted_noisy.jsonl" `
  -OutputCleanJsonl "output/original_clean.jsonl" `
  -MaxRows 1000 `
  -Join "outer"
```

## Binary Karşılaştırma

Radyasyon etkisiyle değişen değerleri bit seviyesinde incelemek için:

```bat
compare_binary.bat
```

Detaylı kılavuz: [BINARY_COMPARE_GUIDE.md](BINARY_COMPARE_GUIDE.md)

## JSONL Şema Özeti

Simülasyon kayıtlarında temel alanlar:
- `timestamp`
- `channels.clean`
- `channels.noisy`
- `labels.is_radiation_event`
- `labels.event_type`
- `labels.severity`

Varsayılan event tipleri: `spike`, `bit_flip_like`.
