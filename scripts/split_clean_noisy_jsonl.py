from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tek JSONL girdisinden temiz ve kirli JSONL dosyalari uretir."
    )
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--output-noisy-jsonl", required=True)
    parser.add_argument("--output-clean-jsonl", required=True)
    parser.add_argument(
        "--channels",
        required=True,
        help="Virgulle ayrilmis kanal listesi. Ornek: channel_1,channel_9,channel_12",
    )
    return parser.parse_args()


def parse_channels(channels_arg: str) -> List[str]:
    channels = [c.strip() for c in channels_arg.split(",") if c.strip()]
    if len(channels) < 1:
        raise ValueError("En az 1 kanal vermen gerekiyor.")
    return channels


def load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def extract_record_pair(
    record: Dict[str, Any], output_fields: List[str]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    timestamp = record.get("timestamp")

    noisy_data: Dict[str, Any] = {}
    clean_data: Dict[str, Any] = {}

    channels = record.get("channels")
    if isinstance(channels, dict):
        clean_block = channels.get("clean", {})
        noisy_block = channels.get("noisy", {})
        if isinstance(clean_block, dict):
            clean_data.update(clean_block)
        if isinstance(noisy_block, dict):
            noisy_data.update(noisy_block)

    if not noisy_data:
        for k, v in record.items():
            if k in {"timestamp", "radiation_level", "labels", "channels", "radiation_event"}:
                continue
            if k.endswith("_original"):
                continue
            noisy_data[k] = v

    if not clean_data:
        for k, v in record.items():
            if k.endswith("_original"):
                clean_data[k.removesuffix("_original")] = v
        if not clean_data:
            clean_data.update(noisy_data)

    noisy_out: Dict[str, Any] = {
        "timestamp": timestamp,
        "channels": [
            {"name": field, "value": noisy_data.get(field)}
            for field in output_fields
        ],
    }
    clean_out: Dict[str, Any] = {
        "timestamp": timestamp,
        "channels": [
            {"name": field, "value": clean_data.get(field)}
            for field in output_fields
        ],
    }

    return noisy_out, clean_out


def write_jsonl(records: Iterable[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    channels = parse_channels(args.channels)
    input_path = Path(args.input_jsonl)
    output_noisy = Path(args.output_noisy_jsonl)
    output_clean = Path(args.output_clean_jsonl)

    noisy_records = []
    clean_records = []
    for rec in load_jsonl(input_path):
        noisy, clean = extract_record_pair(rec, channels)
        noisy_records.append(noisy)
        clean_records.append(clean)

    write_jsonl(noisy_records, output_noisy)
    write_jsonl(clean_records, output_clean)

    print("JSONL ayristirma tamamlandi.")
    print(f"Kirli: {output_noisy}")
    print(f"Temiz: {output_clean}")
    print(f"Kayit sayisi: {len(noisy_records)}")


if __name__ == "__main__":
    main()
