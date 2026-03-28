# Binary Veri Karşılaştırma Kılavuzu

Bu araç, radyasyon etkisiyle kirlenmiş telemetri verisinin **orijinal** ve **kirlenmiş** hallerini **binary (bit) seviyesinde** karşılaştırmanızı sağlar.

## 🎯 Özellikler

- **IEEE 754 Binary Gösterim**: Floating-point sayıların 32-bit veya 64-bit binary formatı
- **Bit-Level Karşılaştırma**: Hangi bitlerin değiştiğini gösterir
- **Renkli Vurgulama**: Değişen bitler kırmızı ile işaretlenir
- **Hexadecimal Gösterim**: Her iki değerin hex formatı
- **IEEE 754 Analizi**: Değişikliğin sign, exponent veya mantissa hangi bölümünde olduğu
- **Otomatik Filtreleme**: Sadece radyasyon etkisi olan kayıtları gösterir

## 🚀 Hızlı Başlangıç

### 1. Test Simülasyonu Çalıştır

```bash
python scripts\test_binary_simulation.py
```

Bu komut:
- Küçük bir test dataseti oluşturur
- Radyasyon eventleri simüle eder
- Orijinal ve kirlenmiş değerleri kaydeder
- `output/test_binary_compare.jsonl` dosyasını üretir

### 2. Binary Karşılaştırma Yap

```bash
python scripts\compare_binary_data.py --input-jsonl output\test_binary_compare.jsonl
```

## 📋 Komut Parametreleri

```bash
python scripts\compare_binary_data.py [OPSIYONLAR]

Zorunlu:
  --input-jsonl PATH        Simüle edilmiş telemetri JSONL dosyası

Opsiyonel:
  --max-samples N           Gösterilecek maksimum örnek sayısı (default: 5)
  --precision {32bit,64bit} Binary gösterim hassasiyeti (default: 32bit)
  --show-all                Tüm kanalları göster (sadece değişenleri değil)
  --no-hex                  Hexadecimal gösterimi atla
```

## 📊 Örnek Çıktı

```
################################################################################
# ÖRNEK 1/5
################################################################################

⚡ Radyasyon Event Bilgisi:
  Event ID    : evt_001
  Tip         : bit_flip_like
  Şiddet      : medium
  Radyasyon   : 0.185432
  Etkilenen   : channel_12, channel_70

================================================================================
Timestamp: 2000-01-01T00:05:23+00:00
Kanal: channel_12
================================================================================

📊 Ondalık Değerler:
  Orijinal   : 0.3171748200
  Kirlenmiş  : 0.3171752543
  Fark       : 4.343e-07
  Yüzde Fark : 0.000137%

🔢 Hexadecimal:
  Orijinal  : 0x3EA25E9A
  Kirlenmiş : 0x3EA25E9E

💾 Binary (32-bit IEEE 754):
  Değişen bit sayısı: 2/32

  Orijinal  : 00111110 10100010 01011110 10011010
  Kirlenmiş : 00111110 10100010 01011110 10011110

  ⚠️  Kırmızı bitler değişmiş bitleri gösterir

  🔄 Bit flip pozisyonları (0-indexed): [30, 31]

  📋 IEEE 754 Yapısı (32-bit):
     [0]      = Sign bit
     [1-8]    = Exponent (8 bits)
     [9-31]   = Mantissa/Fraction (23 bits)
     Bit 30: Mantissa
     Bit 31: Mantissa
```

## 🔬 IEEE 754 Format Açıklaması

### 32-bit Float (Single Precision)
```
[S][EEEEEEEE][MMMMMMMMMMMMMMMMMMMMMMM]
 ↑     ↑              ↑
 |     |              └─ Mantissa (23 bit)
 |     └──────────────── Exponent (8 bit)
 └────────────────────── Sign (1 bit)
```

### 64-bit Double (Double Precision)
```
[S][EEEEEEEEEEE][MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM]
 ↑       ↑                              ↑
 |       |                              └─ Mantissa (52 bit)
 |       └────────────────────────────── Exponent (11 bit)
 └────────────────────────────────────── Sign (1 bit)
```

## 🎨 Renk Kodları

Terminal çıktısında:
- ⚡ = Radyasyon eventi
- 📊 = Ondalık gösterim
- 🔢 = Hexadecimal
- 💾 = Binary gösterim
- 🔄 = Bit flip pozisyonları
- 📋 = IEEE 754 analizi
- ⚠️ = Uyarı/dikkat
- ✅ = Başarılı/tamamlandı
- 🔴 (Kırmızı text) = Değişen bitler

## 💡 Kullanım Senaryoları

### Senaryo 1: Genel İnceleme
```bash
# İlk 10 radyasyon eventini incele
python scripts\compare_binary_data.py --input-jsonl output\simulated_telemetry.jsonl --max-samples 10
```

### Senaryo 2: Yüksek Hassasiyetli Analiz
```bash
# 64-bit precision ile detaylı analiz
python scripts\compare_binary_data.py --input-jsonl output\simulated_telemetry.jsonl --precision 64bit
```

### Senaryo 3: Tüm Kanalları Göster
```bash
# Etkilenmeyen kanalları da dahil et
python scripts\compare_binary_data.py --input-jsonl output\simulated_telemetry.jsonl --show-all
```

### Senaryo 4: Minimal Çıktı
```bash
# Hex gösterimi olmadan, sadece binary
python scripts\compare_binary_data.py --input-jsonl output\simulated_telemetry.jsonl --no-hex
```

## 📁 Dosya Formatı

JSONL dosyasındaki her satır bir JSON nesnesi içerir:

### Normal Kayıt (Radyasyon Yok)
```json
{
  "timestamp": "2000-01-01T00:00:05+00:00",
  "radiation_level": 0.030218,
  "channel_12": 0.31717482,
  "channel_13": 0.37176356,
  "channel_70": 0.7881527,
  "channel_71": 0.8118464
}
```

### Radyasyon Eventi Kaydı
```json
{
  "timestamp": "2000-01-01T00:05:23+00:00",
  "radiation_level": 0.185432,
  "channel_12": 0.3171752543,
  "channel_13": 0.37176356,
  "channel_70": 0.7923451,
  "channel_71": 0.8118464,
  "radiation_event": {
    "event_id": "evt_001",
    "event_type": "bit_flip_like",
    "severity": "medium",
    "radiation_level": 0.185432,
    "affected_channels": ["channel_12", "channel_70"]
  },
  "channel_12_original": 0.3171748200,
  "channel_70_original": 0.7881527
}
```

**Not**: `*_original` alanları sadece etkilenen kanallar için mevcuttur.

## 🔧 Sorun Giderme

### Problem: "Radyasyon etkisi olan kayıt bulunamadı"
**Çözüm**: Simülasyon parametrelerini artırın:
```python
cfg = SimulationConfig(
    event_coverage=0.05,  # %5'e çıkar
    min_event_duration_sec=1,
    max_event_duration_sec=4
)
```

### Problem: "Dosya bulunamadı"
**Çözüm**: Önce simülasyon çalıştırın:
```bash
python scripts\test_binary_simulation.py
```

### Problem: Renkler görünmüyor
**Çözüm**: Windows Terminal veya modern bir terminal kullanın. CMD eskidir ve ANSI renkleri desteklemeyebilir.

## 📚 Ek Kaynaklar

- [IEEE 754 Floating Point Standard](https://en.wikipedia.org/wiki/IEEE_754)
- [Bit Flips in Space](https://en.wikipedia.org/wiki/Soft_error)
- [Cosmic Ray Effects on Electronics](https://en.wikipedia.org/wiki/Single-event_upset)

## 🤝 Katkıda Bulunma

Projeye katkıda bulunmak için:
1. Yeni özellik ekleyin
2. Test edin
3. Pull request gönderin

---

**Geliştirici**: Astro Hackathon Team  
**Lisans**: MIT  
**Versiyon**: 1.0.0
