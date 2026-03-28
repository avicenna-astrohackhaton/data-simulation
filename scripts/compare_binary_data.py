"""
Binary veri karşılaştırma aracı.
Orijinal ve radyasyonla kirlenmiş verinin binary hallerini yan yana gösterir.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any, Dict, List, Tuple


def float_to_binary(value: float) -> str:
    """Float değeri IEEE 754 binary formatına çevirir (32-bit)."""
    packed = struct.pack('!f', value)
    binary = ''.join(f'{byte:08b}' for byte in packed)
    return binary


def double_to_binary(value: float) -> str:
    """Float değeri IEEE 754 binary formatına çevirir (64-bit double precision)."""
    packed = struct.pack('!d', value)
    binary = ''.join(f'{byte:08b}' for byte in packed)
    return binary


def highlight_differences(original: str, corrupted: str) -> Tuple[str, str]:
    """İki binary string arasındaki farkları vurgular (ANSI renk kodlarıyla)."""
    highlighted_orig = []
    highlighted_corr = []
    
    for i, (o, c) in enumerate(zip(original, corrupted)):
        if o != c:
            # Kırmızı renk ile farklı bitleri göster
            highlighted_orig.append(f'\033[91m{o}\033[0m')
            highlighted_corr.append(f'\033[91m{c}\033[0m')
        else:
            highlighted_orig.append(o)
            highlighted_corr.append(c)
    
    return ''.join(highlighted_orig), ''.join(highlighted_corr)


def format_binary_with_spacing(binary: str, group_size: int = 8) -> str:
    """Binary stringi okunabilir gruplar halinde formatlar."""
    groups = [binary[i:i+group_size] for i in range(0, len(binary), group_size)]
    return ' '.join(groups)


def compare_values(
    timestamp: str,
    channel: str,
    original: float,
    corrupted: float,
    precision: str = '32bit',
    show_hex: bool = True
) -> None:
    """Tek bir değer çiftini karşılaştırır ve görüntüler."""
    
    # Binary dönüşüm
    if precision == '64bit':
        orig_bin = double_to_binary(original)
        corr_bin = double_to_binary(corrupted)
        bits = 64
    else:
        orig_bin = float_to_binary(original)
        corr_bin = float_to_binary(corrupted)
        bits = 32
    
    # Fark hesapla
    diff_count = sum(1 for o, c in zip(orig_bin, corr_bin) if o != c)
    
    # Vurgulama
    orig_highlighted, corr_highlighted = highlight_differences(orig_bin, corr_bin)
    
    print(f"\n{'='*80}")
    print(f"Timestamp: {timestamp}")
    print(f"Kanal: {channel}")
    print(f"{'='*80}")
    
    print(f"\n📊 Ondalık Değerler:")
    print(f"  Orijinal   : {original:.10f}")
    print(f"  Kirlenmiş  : {corrupted:.10f}")
    print(f"  Fark       : {abs(original - corrupted):.10e}")
    print(f"  Yüzde Fark : {abs(original - corrupted) / abs(original) * 100 if original != 0 else float('inf'):.6f}%")
    
    if show_hex:
        if precision == '64bit':
            orig_hex = struct.pack('!d', original).hex()
            corr_hex = struct.pack('!d', corrupted).hex()
        else:
            orig_hex = struct.pack('!f', original).hex()
            corr_hex = struct.pack('!f', corrupted).hex()
        
        print(f"\n🔢 Hexadecimal:")
        print(f"  Orijinal  : 0x{orig_hex.upper()}")
        print(f"  Kirlenmiş : 0x{corr_hex.upper()}")
    
    print(f"\n💾 Binary ({bits}-bit IEEE 754):")
    print(f"  Değişen bit sayısı: {diff_count}/{bits}")
    
    if diff_count > 0:
        print(f"\n  Orijinal  : {format_binary_with_spacing(orig_highlighted)}")
        print(f"  Kirlenmiş : {format_binary_with_spacing(corr_highlighted)}")
        print(f"\n  ⚠️  Kırmızı bitler değişmiş bitleri gösterir")
    else:
        print(f"  ✅ İki değer identik (değişiklik yok)")
        print(f"  Binary: {format_binary_with_spacing(orig_bin)}")
    
    # Bit flip pozisyonları
    if diff_count > 0:
        flip_positions = [i for i, (o, c) in enumerate(zip(orig_bin, corr_bin)) if o != c]
        print(f"\n  🔄 Bit flip pozisyonları (0-indexed): {flip_positions}")
        
        # IEEE 754 yapısı analizi (32-bit için)
        if precision == '32bit':
            print(f"\n  📋 IEEE 754 Yapısı (32-bit):")
            print(f"     [0]      = Sign bit")
            print(f"     [1-8]    = Exponent (8 bits)")
            print(f"     [9-31]   = Mantissa/Fraction (23 bits)")
            
            for pos in flip_positions:
                if pos == 0:
                    section = "Sign bit"
                elif 1 <= pos <= 8:
                    section = "Exponent"
                else:
                    section = "Mantissa"
                print(f"     Bit {pos}: {section}")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """JSONL dosyasını yükler."""
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def find_corrupted_records(
    records: List[Dict[str, Any]],
    max_samples: int = 5
) -> List[Dict[str, Any]]:
    """Radyasyon etkisi olan kayıtları bulur."""
    corrupted = []
    for rec in records:
        if rec.get('radiation_event'):
            corrupted.append(rec)
            if len(corrupted) >= max_samples:
                break
    return corrupted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Binary veri karşılaştırma aracı - orijinal vs kirlenmiş"
    )
    parser.add_argument(
        "--input-jsonl",
        required=True,
        help="Simüle edilmiş telemetri JSONL dosyası"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=5,
        help="Gösterilecek maksimum örnek sayısı (default: 5)"
    )
    parser.add_argument(
        "--precision",
        choices=['32bit', '64bit'],
        default='32bit',
        help="Binary gösterim hassasiyeti (default: 32bit)"
    )
    parser.add_argument(
        "--show-all",
        action='store_true',
        help="Tüm kanalları göster (sadece değişenleri değil)"
    )
    parser.add_argument(
        "--no-hex",
        action='store_true',
        help="Hexadecimal gösterimi atla"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_jsonl)
    if not input_path.exists():
        print(f"❌ Hata: Dosya bulunamadı: {input_path}")
        return
    
    print(f"📂 Dosya yükleniyor: {input_path}")
    records = load_jsonl(input_path)
    
    print(f"✅ {len(records)} kayıt yüklendi")
    
    # Kirlenmiş kayıtları bul
    corrupted_records = find_corrupted_records(records, args.max_samples)
    
    if not corrupted_records:
        print("⚠️  Radyasyon etkisi olan kayıt bulunamadı!")
        return
    
    print(f"\n🎯 {len(corrupted_records)} adet kirlenmiş kayıt bulundu (max: {args.max_samples})")
    print(f"🔬 Binary karşılaştırma başlıyor ({args.precision})...\n")
    
    for idx, rec in enumerate(corrupted_records, 1):
        print(f"\n\n{'#'*80}")
        print(f"# ÖRNEK {idx}/{len(corrupted_records)}")
        print(f"{'#'*80}")
        
        timestamp = rec.get('timestamp', 'N/A')
        event_info = rec.get('radiation_event', {})
        
        print(f"\n⚡ Radyasyon Event Bilgisi:")
        print(f"  Event ID    : {event_info.get('event_id', 'N/A')}")
        print(f"  Tip         : {event_info.get('event_type', 'N/A')}")
        print(f"  Şiddet      : {event_info.get('severity', 'N/A')}")
        print(f"  Radyasyon   : {event_info.get('radiation_level', 'N/A'):.6f}")
        
        affected = event_info.get('affected_channels', [])
        print(f"  Etkilenen   : {', '.join(affected) if affected else 'N/A'}")
        
        # Her kanal için karşılaştırma
        channels_to_show = affected if not args.show_all else [k for k in rec.keys() 
                                                                 if k not in ['timestamp', 'radiation_event']]
        
        for channel in channels_to_show:
            if f"{channel}_original" in rec:
                original_val = rec[f"{channel}_original"]
                corrupted_val = rec[channel]
                
                if original_val != corrupted_val or args.show_all:
                    compare_values(
                        timestamp=timestamp,
                        channel=channel,
                        original=original_val,
                        corrupted=corrupted_val,
                        precision=args.precision,
                        show_hex=not args.no_hex
                    )
    
    print(f"\n\n{'='*80}")
    print("✅ Karşılaştırma tamamlandı!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
