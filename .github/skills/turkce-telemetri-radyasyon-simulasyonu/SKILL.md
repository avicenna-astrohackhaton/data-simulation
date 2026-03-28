---
name: turkce-telemetri-radyasyon-simulasyonu
description: 'Genel amaçlı Türkçe iletişim standardını uygula ve Kaggle telemetri verisiyle dinamik radyasyon gürültüsü simülasyonu planla. Use when: always Turkish responses, telemetry simulation, radiation noise injection, JSONL schema, event scheduling, transient anomaly, hackathon planning.'
argument-hint: 'Kaggle dataset adı, kanal listesi, event oranı ve çıktı formatı (varsayılan JSONL) verin.'
user-invocable: true
disable-model-invocation: false
---

# Türkçe Telemetri Radyasyon Simülasyonu

## Amaç
Bu skill, Kaggle’dan gelen telemetri verisine tüm satırları kirletmeden, yalnızca dinamik seçilen zaman pencerelerinde radyasyon olayı enjekte eden bir veri hattı kurar.
Ek olarak, kullanıcıya dönük tüm iletişimde Türkçe dil standardını korur.

## Ne Zaman Kullanılır
- Telemetri verisinde radyasyon etkisini gerçekçi biçimde simüle etmek istediğinde
- Anlık (transient) bozulmaları event tabanlı üretmek istediğinde
- `timestamp`, `channels.clean`, `channels.noisy`, `radiation_level`, `labels` alanlarıyla JSON akışı hazırlamak istediğinde
- Hackathon için hızlı ama mühendislik olarak tutarlı bir MVP çıkarmak istediğinde

## Dil Kuralı
- Tüm açıklamalar, planlar, çıktı mesajları ve kullanıcıya dönük metinler Türkçe üretilir.
- Kod içi yorumlar kısa tutulur; yalnızca gerekli yerde eklenir.
- İngilizce teknik terim gerekiyorsa Türkçe karşılığıyla birlikte kullanılır.

## Girdiler
- Kaggle veri kaynağı (dosya veya dataset)
- Kanal listesi (öneri: 3-4 kanal)
- Örnekleme frekansı (varsayılan: 1 Hz)
- Event oranı ve süre sınırları
- Çıktı hedefi (JSON/JSONL)
- Çıktı hedefi verilmemişse varsayılan `JSONL` kullanılır.

## Prosedür
1. Veri setini doğrula:
- Zaman sütunu ve en az 3 sayısal kanal var mı kontrol et.
- Eksik veya bozuk satırları işaretle.

2. Şemayı sabitle:
- Ortak kanal isimlerini belirle.
- Fiziksel min-max sınırlarını kanal bazında tanımla.

3. Event planını üret:
- Toplam örneklerin küçük bir yüzdesinde event penceresi aç.
- Event sürelerini kısa tut (ör. 1-4 saniye).
- Eventler arası minimum boşluk koy (cooldown).

4. Radyasyon kanalı ekle:
- Event dışı `radiation_level` baseline seviyede olsun.
- Event sırasında severity’ye göre yükselt.

5. Seçili kanallarda transient etki uygula:
- Event sırasında spike/drop/bit_flip_like etkilerinden birini uygula.
- Event bitince seri normale dönsün.
- Değerleri kanal min-max aralığında clamp et.

6. Etiketle:
- `is_radiation_event`
- `event_type` (`spike`, `drop`, `bit_flip_like`, `none`)
- `severity` (`low`, `medium`, `high`, `none`)

7. JSON çıktıyı üret:
- Her satır tek timestamp temsil etsin.
- `channels.clean` ve `channels.noisy` aynı kanal anahtarlarını içersin.
 - Varsayılan akış biçimi `JSONL` olsun.

8. Doğrulama yap:
- Event coverage hedef aralıkta mı?
- Non-event bölgede clean/noisy farkı düşük mü?
- Event anında radiation ve kanal etkisi gözleniyor mu?
- Aynı seed ile aynı çıktı yeniden üretiliyor mu?

## Çıkış Kriterleri
- Çıktı JSON şeması tutarlı
- Event etiketleri eksiksiz
- Deterministik yeniden üretim başarılı
- Entegrasyona hazır örnek payload mevcut

## Hızlı Parametre Profili (MVP)
- `seed`: 42
- `event_coverage`: %2 (önerilen aralık %1-%3)
- `event_duration_sec`: 1-4
- `event_cooldown_sec`: 20
- `severity_distribution`: low %60, medium %30, high %10
- `event_type_distribution`: spike %70, bit_flip_like %30
