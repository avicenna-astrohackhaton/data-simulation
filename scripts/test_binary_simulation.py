#!/usr/bin/env python3
"""
Test simülasyonu - binary karşılaştırma için demo
"""

import sys
from pathlib import Path

# src klasörünü path'e ekle
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from simulation.radiation_simulator import (
    SimulationConfig,
    load_and_prepare,
    simulate_dynamic_radiation,
    to_jsonl_records,
    write_jsonl,
    compute_summary,
)
import json

def main():
    # Test için küçük bir dataset kullan
    input_csv = Path("data/processed/mission1_flat.csv")
    
    if not input_csv.exists():
        print(f"❌ Hata: {input_csv} bulunamadı!")
        print("Önce `run.bat` veya `run.ps1` ile veri üretmelisiniz.")
        return
    
    channels = ["channel_12", "channel_13", "channel_70", "channel_71"]
    
    print("🚀 Test simülasyonu başlatılıyor...")
    print(f"📂 Input: {input_csv}")
    print(f"📊 Kanallar: {', '.join(channels)}")
    
    cfg = SimulationConfig(
        sampling_hz=1,
        seed=42,
        event_coverage=0.05,  # Daha fazla event görmek için
        min_event_duration_sec=1,
        max_event_duration_sec=3,
        event_cooldown_sec=10,
    )
    
    prepared = load_and_prepare(
        input_csv=input_csv,
        channels=channels,
        timestamp_col=None,
        sampling_hz=cfg.sampling_hz,
        max_rows=1000,  # Test için sadece 1000 satır
    )
    
    print(f"✅ {len(prepared)} satır veri yüklendi")
    
    simulated = simulate_dynamic_radiation(
        prepared=prepared,
        channels=channels,
        cfg=cfg,
    )
    
    records = to_jsonl_records(simulated, channels=channels)
    output_path = Path("output/test_binary_compare.jsonl")
    write_jsonl(records, output_path)
    
    summary = compute_summary(simulated)
    
    print(f"\n✅ Simülasyon tamamlandı!")
    print(f"📁 Çıktı: {output_path}")
    print(f"\n📈 Özet:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    # Radyasyon eventi olan kayıtları say
    event_records = [r for r in records if 'radiation_event' in r]
    print(f"\n⚡ Radyasyon eventi olan kayıt sayısı: {len(event_records)}")
    
    if event_records:
        print(f"\n🔍 İlk event örneği:")
        first_event = event_records[0]
        print(f"  Timestamp: {first_event['timestamp']}")
        event_info = first_event['radiation_event']
        print(f"  Event ID: {event_info['event_id']}")
        print(f"  Tip: {event_info['event_type']}")
        print(f"  Şiddet: {event_info['severity']}")
        print(f"  Etkilenen kanallar: {', '.join(event_info['affected_channels'])}")
        
        for ch in event_info['affected_channels']:
            if f"{ch}_original" in first_event:
                print(f"    {ch}:")
                print(f"      Orijinal: {first_event[f'{ch}_original']}")
                print(f"      Kirlenmiş: {first_event[ch]}")
    
    print(f"\n💡 Binary karşılaştırma için:")
    print(f"   python scripts\\compare_binary_data.py --input-jsonl {output_path}")

if __name__ == "__main__":
    main()
