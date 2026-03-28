# Data Simulation MVP

Bu repo, Kaggle telemetri verisine dinamik radyasyon eventleri ekleyip JSONL akisi uretir.

## ✨ Yeni Özellik: Binary Veri Karşılaştırma

**Radyasyon etkisiyle kirlenmiş verinin orijinal haliyle bit-seviyesinde karşılaştırması!**

```bash
# Test simülasyonu çalıştır
python scripts\test_binary_simulation.py

# Binary karşılaştırma yap
python scripts\compare_binary_data.py --input-jsonl output\test_binary_compare.jsonl
```

📖 **Detaylı kılavuz**: [BINARY_COMPARE_GUIDE.md](BINARY_COMPARE_GUIDE.md)

### Ne Gösterir?
- 📊 Ondalık değer farkları
- 🔢 Hexadecimal gösterim
- 💾 32-bit/64-bit IEEE 754 binary format
- 🔄 Bit flip pozisyonları (hangi bitler değişmiş)
- 📋 Sign/Exponent/Mantissa analizi
- ⚠️ Renkli vurgulama (değişen bitler kırmızı)

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Tek Komutla Calistirma

Tum akisi (ESA ham veri -> flat CSV -> radyasyonlu JSONL) tek komutta calistirabilirsiniz:

```powershell
.\run.ps1
```

Alternatif (CMD/PowerShell fark etmez):

```bash
run.bat
```

Isterseniz parametre verebilirsiniz:

```powershell
.\run.ps1 -MissionRoot "data/raw/ESA-Mission2/ESA-Mission2" -Channels "channel_2,channel_19,channel_98,channel_99" -FlatCsv "data/processed/mission2_flat.csv" -OutputJsonl "output/mission2_simulated.jsonl" -MaxRows 300000

Not: Varsayilan optimize kanal seti su sekildedir:
channel_41,channel_42,channel_43,channel_44,channel_45,channel_46,channel_14,channel_21,channel_29,channel_48,channel_47,channel_49,channel_52,channel_51,channel_50,channel_22,channel_31,channel_39,channel_15,channel_23
```

## Calistirma

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run.ps1 -MaxRows 1000 -FlatCsv "data/processed/mission1_1000.csv"

```bash
$env:PYTHONPATH="src"
python scripts/run_simulation.py \
  --input-csv "data/raw/telemetry.csv" \
  --channels "battery_voltage,temperature,roll,yaw" \
  --timestamp-col "timestamp" \
  --output-jsonl "output/simulated_telemetry.jsonl"
```

## ESA Ham Veriden Flat CSV Uretme

ESA-Mission verisi dogrudan tek CSV olmadigi icin once converter calistirin:

```bash
python scripts/convert_esa_to_flat_csv.py \
  --mission-root "data/raw/ESA-Mission1/ESA-Mission1" \
  --channels "channel_41,channel_42,channel_43,channel_44,channel_45,channel_46,channel_14,channel_21,channel_29,channel_48,channel_47,channel_49,channel_52,channel_51,channel_50,channel_22,channel_31,channel_39,channel_15,channel_23" \
  --output-csv "data/processed/mission1_flat.csv" \
  --join "outer" \
  --max-rows 300000
```

Sonra simulasyonu uretin:

```bash
$env:PYTHONPATH="src"
python scripts/run_simulation.py \
  --input-csv "data/processed/mission1_flat.csv" \
  --channels "channel_41,channel_42,channel_43,channel_44,channel_45,channel_46,channel_14,channel_21,channel_29,channel_48,channel_47,channel_49,channel_52,channel_51,channel_50,channel_22,channel_31,channel_39,channel_15,channel_23" \
  --timestamp-col "timestamp" \
  --output-jsonl "output/simulated_telemetry.jsonl"
```

## Binary Veri Karşılaştırma

Radyasyon etkisiyle kirlenmiş verinin orijinal haliyle **binary seviyesinde** karşılaştırmasını görmek için:

```bash
compare_binary.bat
```

veya doğrudan:

```bash
python scripts\compare_binary_data.py --input-jsonl output\simulated_telemetry.jsonl --max-samples 5 --precision 32bit
```

### Karşılaştırma Aracı Özellikleri

Bu araç şunları gösterir:
- 📊 **Ondalık değerler**: Orijinal ve kirlenmiş değerlerin ondalık gösterimi
- 🔢 **Hexadecimal**: Her iki değerin hex formatı
- 💾 **Binary (IEEE 754)**: 32-bit veya 64-bit binary gösterim
- 🔄 **Bit flip pozisyonları**: Hangi bitlerin değiştiği
- ⚠️ **Renkli vurgulama**: Değişen bitler kırmızı ile gösterilir
- 📋 **IEEE 754 analizi**: Değişikliğin sign/exponent/mantissa hangi bölümünde olduğu

### Parametreler

```bash
--input-jsonl    : JSONL dosya yolu (zorunlu)
--max-samples    : Gösterilecek maksimum örnek sayısı (default: 5)
--precision      : 32bit veya 64bit (default: 32bit)
--show-all       : Tüm kanalları göster (sadece değişenleri değil)
--no-hex         : Hexadecimal gösterimi atla
```

### Örnek Çıktı

```
⚡ Radyasyon Event Bilgisi:
  Event ID    : evt_001
  Tip         : bit_flip_like
  Şiddet      : high
  Radyasyon   : 0.245000

📊 Ondalık Değerler:
  Orijinal   : 3.1415926535
  Kirlenmiş  : 3.1415932178
  Fark       : 5.643e-07
  
💾 Binary (32-bit IEEE 754):
  Değişen bit sayısı: 2/32
  
  Orijinal  : 01000000 01001001 00001111 11011011
  Kirlenmiş : 01000000 01001001 00001111 11011111
  
  🔄 Bit flip pozisyonları: [30, 31]
     Bit 30: Mantissa
     Bit 31: Mantissa
```

## Cikti Semasi

Her satir bir JSON kaydidir:
- timestamp
- channels.clean
- channels.noisy
- radiation_level
- labels.is_radiation_event
- labels.event_type
- labels.severity

Not: Varsayilan event tipleri `spike` ve `bit_flip_like` olarak uretilir.
