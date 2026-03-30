# Data Simulation MVP

ESA uydu telemetri verisine **dinamik radyasyon eventleri** ekleyip deterministik JSONL akışı üreten veri simülasyon altyapısı.

## 📁 Proje Yapısı

```
data-simulation/
├── src/simulation/
│   └── radiation_simulator.py   # Temel simülasyon motoru
├── scripts/
│   ├── convert_esa_to_flat_csv.py   # ESA ham veri → düz CSV
│   ├── run_simulation.py            # Radyasyon simülasyonu → JSONL
│   └── split_clean_noisy_jsonl.py   # Tek JSONL → temiz + kirli JSONL
├── output/                          # Üretilen çıktı dosyaları
├── requirements.txt
├── run.ps1                          # Tam pipeline (PowerShell)
└── run.bat                          # Tam pipeline (CMD/PowerShell sarmalayıcı)
```

## ⚙️ Kurulum

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# veya: source .venv/bin/activate  # Linux / macOS
pip install -r requirements.txt
```

## 🚀 Tek Komutla Tam Pipeline

Tüm adımları (ESA ham veri → flat CSV → radyasyonlu JSONL → temiz/kirli ayrımı) tek komutta çalıştırın:

```powershell
.\run.ps1
```

CMD veya PowerShell fark etmeksizin:

```bat
run.bat
```

### run.ps1 Parametreleri

| Parametre | Varsayılan | Açıklama |
|-----------|-----------|----------|
| `-MissionRoot` | `data/raw/ESA-Mission1/ESA-Mission1` | ESA ham veri kök dizini |
| `-Channels` | *(optimize kanal seti, aşağıya bakın)* | Virgülle ayrılmış kanal listesi |
| `-FlatCsv` | `data/processed/mission1_flat.csv` | Ara CSV çıktı yolu |
| `-OutputJsonl` | `output/simulated_telemetry.jsonl` | Tam simülasyon JSONL çıktısı |
| `-OutputNoisyJsonl` | `output/corrupted_noisy.jsonl` | Yalnızca kirli kanal değerleri |
| `-OutputCleanJsonl` | `output/original_clean.jsonl` | Yalnızca temiz kanal değerleri |
| `-MaxRows` | `300000` | İşlenecek maksimum satır sayısı |
| `-Join` | `outer` | CSV birleştirme stratejisi (`outer` / `inner`) |

**Örnek — farklı mission ile çalıştırmak:**

```powershell
.\run.ps1 `
  -MissionRoot "data/raw/ESA-Mission2/ESA-Mission2" `
  -Channels "channel_2,channel_19,channel_98,channel_99" `
  -FlatCsv "data/processed/mission2_flat.csv" `
  -OutputJsonl "output/mission2_simulated.jsonl" `
  -MaxRows 300000
```

**Hızlı test (küçük veri seti):**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run.ps1 -MaxRows 1000 -FlatCsv "data/processed/mission1_1000.csv"
```

---

## 🔧 Adım Adım Manuel Çalıştırma

### Adım 1 — ESA Ham Veri → Flat CSV

ESA-Mission verisi tek CSV olarak gelmiyor; önce dönüştürücüyü çalıştırın:

```bash
# Optimize kanal seti için aşağıdaki "Optimize Kanal Seti" bölümüne bakın.
CHANNELS="channel_41,channel_42,channel_43,channel_44,channel_45,channel_46,channel_14,channel_21,channel_29,channel_48,channel_47,channel_49,channel_52,channel_51,channel_50,channel_22,channel_31,channel_39,channel_15,channel_23"

python scripts/convert_esa_to_flat_csv.py \
  --mission-root "data/raw/ESA-Mission1/ESA-Mission1" \
  --channels "$CHANNELS" \
  --output-csv "data/processed/mission1_flat.csv" \
  --join "outer" \
  --max-rows 300000
```

### Adım 2 — Radyasyon Simülasyonu → JSONL

```bash
$env:PYTHONPATH="src"
python scripts/run_simulation.py \
  --input-csv "data/processed/mission1_flat.csv" \
  --channels "$CHANNELS" \
  --timestamp-col "timestamp" \
  --output-jsonl "output/simulated_telemetry.jsonl"
```

### Adım 3 — Tek JSONL → Temiz + Kirli Ayrımı

```bash
$env:PYTHONPATH="src"
python scripts/split_clean_noisy_jsonl.py \
  --input-jsonl "output/simulated_telemetry.jsonl" \
  --output-noisy-jsonl "output/corrupted_noisy.jsonl" \
  --output-clean-jsonl "output/original_clean.jsonl" \
  --channels "$CHANNELS"
```

---

## 📊 Çıktı Dosyaları ve Şemalar

### `output/simulated_telemetry.jsonl` — Tam Simülasyon

Her satır bir zaman damgasını temsil eden JSON kaydıdır:

```json
{
  "timestamp": 1000,
  "channels": {
    "clean": { "channel_41": 0.512, "channel_42": -1.034 },
    "noisy": { "channel_41": 0.512, "channel_42": -1.187 }
  },
  "radiation_level": 0.031,
  "labels": {
    "is_radiation_event": false,
    "event_type": "none",
    "severity": "none"
  }
}
```

### `output/original_clean.jsonl` — Temiz Kanallar

```json
{
  "timestamp": 1000,
  "channels": [
    { "name": "channel_41", "value": 0.512 },
    { "name": "channel_42", "value": -1.034 }
  ]
}
```

### `output/corrupted_noisy.jsonl` — Kirlenmiş Kanallar

```json
{
  "timestamp": 1000,
  "channels": [
    { "name": "channel_41", "value": 0.512 },
    { "name": "channel_42", "value": -1.187 }
  ]
}
```

### Alan Açıklamaları

| Alan | Tür | Açıklama |
|------|-----|----------|
| `timestamp` | int | Örnekleme anı (saniye cinsinden indeks) |
| `channels.clean` | dict | Radyasyon etkisi uygulanmamış orijinal kanal değerleri |
| `channels.noisy` | dict | Radyasyon etkisiyle bozulmuş kanal değerleri |
| `radiation_level` | float | Anlık radyasyon seviyesi (baseline ≈ 0.03) |
| `labels.is_radiation_event` | bool | Bu örnek bir radyasyon eventi mi? |
| `labels.event_type` | string | `spike`, `bit_flip_like` veya `none` |
| `labels.severity` | string | `low`, `medium`, `high` veya `none` |

---

## 🎛️ Simülasyon Parametreleri (MVP Profili)

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| `seed` | `42` | Deterministik yeniden üretim için sabit tohum |
| `event_coverage` | `%2` | Tüm örneklerin radyasyon event'i olan oranı (%1–%3 önerilir) |
| `event_duration_sec` | `1–4 s` | Her event penceresi süresi |
| `event_cooldown_sec` | `20 s` | Eventler arasındaki minimum bekleme süresi |
| `sampling_hz` | `1 Hz` | Örnekleme frekansı |
| **Severity dağılımı** | low %60 / medium %30 / high %10 | Şiddet seviyesi olasılıkları |
| **Event tipi dağılımı** | spike %70 / bit_flip_like %30 | Bozulma tipi olasılıkları |

### Optimize Kanal Seti (Varsayılan)

```
channel_41, channel_42, channel_43, channel_44, channel_45, channel_46,
channel_14, channel_21, channel_29, channel_48, channel_47, channel_49,
channel_52, channel_51, channel_50, channel_22, channel_31, channel_39,
channel_15, channel_23
```

---

## 🔬 Binary Veri Karşılaştırma

Radyasyon etkisiyle kirlenmiş verinin orijinaliyle **bit düzeyinde** karşılaştırması için:

```bash
compare_binary.bat
```

veya doğrudan:

```bash
python scripts\compare_binary_data.py \
  --input-jsonl output\simulated_telemetry.jsonl \
  --max-samples 5 \
  --precision 32bit
```

### Binary Karşılaştırma Parametreleri
| `--max-samples` | Gösterilecek maksimum örnek sayısı (varsayılan: 5) |
| `--precision` | `32bit` veya `64bit` (varsayılan: `32bit`) |
| `--show-all` | Tüm kanalları göster (yalnızca değişenler değil) |
| `--no-hex` | Hexadecimal gösterimi atla |

### Karşılaştırma Aracının Gösterdikleri

- 📊 **Ondalık değerler** — orijinal ve kirlenmiş arasındaki fark
- 🔢 **Hexadecimal gösterim** — her iki değerin hex formatı
- 💾 **Binary (IEEE 754)** — 32-bit veya 64-bit binary gösterim
- 🔄 **Bit flip pozisyonları** — hangi bitlerin değiştiği
- ⚠️ **Renkli vurgulama** — değişen bitler kırmızı ile işaretlenir
- 📋 **IEEE 754 analizi** — değişikliğin sign / exponent / mantissa bölümü

📖 **Detaylı kılavuz**: [BINARY_COMPARE_GUIDE.md](BINARY_COMPARE_GUIDE.md)

---

## ✅ Doğrulama Kontrol Listesi

Simülasyon çıktısını aşağıdaki kriterlerle doğrulayın:

- [ ] Event coverage hedef aralıkta mı? (%1–%3)
- [ ] Event dışı bölgelerde `clean` / `noisy` farkı düşük mü?
- [ ] Event anında `radiation_level` yükselmiş mi?
- [ ] Kanal değerlerinde spike veya bit_flip_like etkisi gözleniyor mu?
- [ ] Aynı `seed` ile aynı çıktı yeniden üretiliyor mu?
