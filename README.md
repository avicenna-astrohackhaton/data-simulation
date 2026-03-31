# 🛰️ Avicenna Astro Hackathon — Veri Simülasyon Modülü

ESA uydu telemetri verisine **dinamik radyasyon olayları** enjekte eden ve gerçekçi **kirli/temiz veri çiftleri** üreten veri hattı.

---

## 📋 İçindekiler

- [Proje Hakkında](#-proje-hakkında)
- [Veri Akışı](#-veri-akışı)
- [Proje Yapısı](#-proje-yapısı)
- [Kurulum](#-kurulum)
- [Hızlı Başlangıç](#-hızlı-başlangıç)
- [Adım Adım Kullanım](#-adım-adım-kullanım)
- [Simülasyon Parametreleri](#-simülasyon-parametreleri)
- [Çıktı Şeması](#-çıktı-şeması)
- [Binary Karşılaştırma Aracı](#-binary-karşılaştırma-aracı)
- [Varsayılan Kanal Listesi](#-varsayılan-kanal-listesi)
- [Sorun Giderme](#-sorun-giderme)

---

## 🎯 Proje Hakkında

Bu modül, ESA uydu görev verilerine gerçekçi radyasyon gürültüsü ekleyerek makine öğrenmesi modelleri için etiketli eğitim verisi üretir.

**Temel özellikler:**

- 🔬 Dinamik radyasyon olay penceresi seçimi (deterministik, `seed` ile yeniden üretilebilir)
- ⚡ `spike`, `bit_flip_like` olay tipleri
- 📊 Kanal bazlı clamp ile gerçekçi değer aralıkları
- 🗂️ Aynı anda temiz ve kirli JSONL çıktısı
- 💾 IEEE 754 bit-seviyesi karşılaştırma aracı

---

## 🔄 Veri Akışı

```
ESA Ham Veri (çoklu CSV)
        │
        ▼
[1] convert_esa_to_flat_csv.py
        │  → data/processed/mission1_flat.csv
        ▼
[2] run_simulation.py
        │  → output/simulated_telemetry.jsonl  (temiz + kirli + etiketler)
        ▼
[3] split_clean_noisy_jsonl.py
        ├─ output/original_clean.jsonl
        └─ output/corrupted_noisy.jsonl
```

---

## 📁 Proje Yapısı

```
data-simulation/
├── src/
│   └── simulation/
│       ├── __init__.py
│       └── radiation_simulator.py   # Çekirdek simülasyon mantığı
├── scripts/
│   ├── convert_esa_to_flat_csv.py   # ESA ham veri → düz CSV dönüştürücü
│   ├── run_simulation.py            # Radyasyon simülasyonu çalıştırıcı
│   └── split_clean_noisy_jsonl.py   # JSONL'yi temiz/kirli olarak ayırır
├── output/                          # Üretilen JSONL dosyaları
├── run.ps1                          # Tek komutlu PowerShell orkestratörü
├── run.bat                          # Tek komutlu Batch wrapper
├── compare_binary.bat               # Binary karşılaştırma kısayolu
├── requirements.txt
└── BINARY_COMPARE_GUIDE.md         # Binary karşılaştırma detaylı kılavuzu
```

---

## ⚙️ Kurulum

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat

pip install -r requirements.txt
```

**Gereksinimler:** Python 3.10+, `pandas >= 2.0.0`, `numpy >= 1.24.0`

---

## 🚀 Hızlı Başlangıç

Tüm akışı (ESA ham veri → düz CSV → radyasyonlu JSONL → temiz/kirli ayrımı) **tek komutla** çalıştırın:

```powershell
# PowerShell (varsayılan parametrelerle ESA Mission 1)
.\run.ps1

# Execution Policy hatası alırsanız
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run.ps1
```

```batch
:: CMD ile
run.bat
```

**Parametreli kullanım örneği:**

```powershell
.\run.ps1 `
  -MissionRoot "data/raw/ESA-Mission2/ESA-Mission2" `
  -FlatCsv     "data/processed/mission2_flat.csv" `
  -OutputJsonl "output/mission2_simulated.jsonl" `
  -MaxRows     300000
```

Komut tamamlandığında üç dosya üretilir:

| Dosya | İçerik |
|---|---|
| `output/simulated_telemetry.jsonl` | Temiz + kirli + etiket (ara çıktı) |
| `output/original_clean.jsonl` | Yalnızca temiz kanal değerleri |
| `output/corrupted_noisy.jsonl` | Yalnızca kirlenmiş kanal değerleri |

---

## 📖 Adım Adım Kullanım

### Adım 1 — ESA Ham Veri → Düz CSV

ESA görev verisi birden fazla kanal dosyasına bölünmüş olarak gelir. Önce tek bir düz CSV'ye dönüştürün:

```bash
python scripts/convert_esa_to_flat_csv.py \
  --mission-root "data/raw/ESA-Mission1/ESA-Mission1" \
  --channels "channel_41,channel_42,channel_43,channel_44,channel_45,channel_46,channel_14,channel_21,channel_29,channel_48,channel_47,channel_49,channel_52,channel_51,channel_50,channel_22,channel_31,channel_39,channel_15,channel_23" \
  --output-csv "data/processed/mission1_flat.csv" \
  --join "outer" \
  --max-rows 300000
```

### Adım 2 — Radyasyon Simülasyonu

```bash
$env:PYTHONPATH="src"
python scripts/run_simulation.py \
  --input-csv "data/processed/mission1_flat.csv" \
  --channels "channel_41,channel_42,channel_43,channel_44,channel_45,channel_46,channel_14,channel_21,channel_29,channel_48,channel_47,channel_49,channel_52,channel_51,channel_50,channel_22,channel_31,channel_39,channel_15,channel_23" \
  --timestamp-col "timestamp" \
  --output-jsonl "output/simulated_telemetry.jsonl"
```

### Adım 3 — Temiz / Kirli JSONL Ayrımı

```bash
python scripts/split_clean_noisy_jsonl.py \
  --input-jsonl "output/simulated_telemetry.jsonl" \
  --output-noisy-jsonl "output/corrupted_noisy.jsonl" \
  --output-clean-jsonl "output/original_clean.jsonl"
```

---

## 🔧 Simülasyon Parametreleri

`run_simulation.py` aşağıdaki argümanları kabul eder:

| Parametre | Varsayılan | Açıklama |
|---|---|---|
| `--input-csv` | *(zorunlu)* | Girdi düz CSV dosyası |
| `--output-jsonl` | `output/simulated_telemetry.jsonl` | Çıktı JSONL yolu |
| `--channels` | Varsayılan liste | Virgülle ayrılmış kanal isimleri |
| `--timestamp-col` | Otomatik tespit | Zaman damgası sütunu adı |
| `--sampling-hz` | `1` | Örnekleme frekansı (Hz) |
| `--seed` | `42` | Rastgelelik tohumu (yeniden üretim için) |
| `--event-coverage` | `0.02` | Hedef olay kapsamı (toplam örneklerin %2'si) |
| `--min-event-duration` | `1` | Minimum olay süresi (saniye) |
| `--max-event-duration` | `4` | Maksimum olay süresi (saniye) |
| `--cooldown-sec` | `20` | Olaylar arası minimum bekleme (saniye) |
| `--max-rows` | Tümü | İşlenecek maksimum satır sayısı |
| `--output-format` | `jsonl` | Çıktı biçimi: `jsonl` veya `json` |

**Varsayılan olay dağılımı:**

| Parametre | Değer |
|---|---|
| Şiddet (severity) | Düşük %60, Orta %30, Yüksek %10 |
| Olay tipi (event_type) | Spike %70, Bit-flip benzeri %30 |

---

## 📄 Çıktı Şeması

### `simulated_telemetry.jsonl` — Her satır bir zaman damgasını temsil eder

**Normal kayıt (radyasyon olayı yok):**

```json
{
  "timestamp": "2000-01-01T00:00:05+00:00",
  "channels": {
    "clean": { "channel_41": 1.234, "channel_42": 0.567 },
    "noisy": { "channel_41": 1.234, "channel_42": 0.567 }
  },
  "labels": {
    "is_radiation_event": false,
    "event_type": "none",
    "severity": "none"
  }
}
```

**Radyasyon olayı kaydı:**

```json
{
  "timestamp": "2000-01-01T00:05:23+00:00",
  "channels": {
    "clean": { "channel_41": 1.234, "channel_42": 0.567 },
    "noisy": { "channel_41": 1.891, "channel_42": 0.567 }
  },
  "labels": {
    "is_radiation_event": true,
    "event_type": "spike",
    "severity": "medium"
  },
  "radiation_event": {
    "event_id": "evt_001",
    "event_type": "spike",
    "severity": "medium",
    "affected_channels": ["channel_41"]
  },
  "channel_41_original": 1.234
}
```

### `original_clean.jsonl` ve `corrupted_noisy.jsonl`

```json
{
  "timestamp": "2000-01-01T00:05:23+00:00",
  "channels": [
    { "name": "channel_41", "value": 1.891 },
    { "name": "channel_42", "value": 0.567 }
  ]
}
```

---

## 🔬 Binary Karşılaştırma Aracı

Radyasyon etkisiyle kirlenmiş verinin orijinal haliyle **bit seviyesinde** karşılaştırmasını yapın:

```bash
# Kısayol (yalnızca Windows)
compare_binary.bat
```

```bash
# Çapraz platform (Windows / macOS / Linux)
python scripts/compare_binary_data.py \
  --input-jsonl output/simulated_telemetry.jsonl \
  --max-samples 5 \
  --precision 32bit
```

**Parametreler:**

| Parametre | Varsayılan | Açıklama |
|---|---|---|
| `--input-jsonl` | *(zorunlu)* | Simüle edilmiş JSONL dosyası |
| `--max-samples` | `5` | Gösterilecek maksimum örnek sayısı |
| `--precision` | `32bit` | `32bit` veya `64bit` IEEE 754 gösterimi |
| `--show-all` | — | Etkilenmeyen kanalları da göster |
| `--no-hex` | — | Hexadecimal gösterimi atla |

**Örnek terminal çıktısı:**

```
⚡ Radyasyon Event Bilgisi:
  Event ID    : evt_001
  Tip         : bit_flip_like
  Şiddet      : medium
  Etkilenen   : channel_41

📊 Ondalık Değerler:
  Orijinal   : 1.2340000000
  Kirlenmiş  : 1.3861732483
  Fark       : 1.522e-01

💾 Binary (32-bit IEEE 754):
  Değişen bit sayısı: 3/32

  Orijinal  : 00111111 10011110 00101110 00010111
  Kirlenmiş : 00111111 10110001 00111010 11100001

  🔄 Bit flip pozisyonları: [8, 14, 22]
     Bit 8:  Exponent
     Bit 14: Mantissa
     Bit 22: Mantissa
```

📖 Daha fazla bilgi: [BINARY_COMPARE_GUIDE.md](BINARY_COMPARE_GUIDE.md)

---

## 📡 Varsayılan Kanal Listesi

Pipeline aşağıdaki 20 optimize edilmiş kanalı kullanır:

```
channel_14, channel_15, channel_21, channel_22, channel_23,
channel_29, channel_31, channel_39, channel_41, channel_42,
channel_43, channel_44, channel_45, channel_46, channel_47,
channel_48, channel_49, channel_50, channel_51, channel_52
```

---

## 🛠️ Sorun Giderme

| Hata | Çözüm |
|---|---|
| `Execution Policy` hatası | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` çalıştırın |
| `Missing channels in input data` | `--channels` listesindeki kanal isimlerini CSV başlıklarıyla karşılaştırın |
| `Input after preprocessing is too short` | `--max-rows` değerini artırın veya daha büyük bir veri seti kullanın |
| Renkler görünmüyor | Windows Terminal veya modern bir terminal emülatörü kullanın |
| `Radyasyon etkisi olan kayıt bulunamadı` | `--event-coverage 0.05` ile kapsamı artırın |

---

**Takım:** Avicenna Astro Hackathon  
**Lisans:** MIT
