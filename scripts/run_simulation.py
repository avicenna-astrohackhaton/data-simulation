# run_simulation.py bu fonksiyonları kullanarak tam bir 
# simülasyon çalıştırır ve çıktı olarak JSONL dosyası üretir.



from __future__ import annotations

import argparse
import json
from pathlib import Path

from simulation.radiation_simulator import (
    SimulationConfig,
    compute_summary,
    load_and_prepare,
    simulate_dynamic_radiation,
    to_jsonl_records,
    write_json,
    write_jsonl,
)


TARGET_CHANNELS = [
    "channel_41",
    "channel_42",
    "channel_43",
    "channel_44",
    "channel_45",
    "channel_46",
    "channel_14",
    "channel_21",
    "channel_29",
    "channel_48",
    "channel_47",
    "channel_49",
    "channel_52",
    "channel_51",
    "channel_50",
    "channel_22",
    "channel_31",
    "channel_39",
    "channel_15",
    "channel_23",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Kaggle telemetri verisinde dinamik radyasyon event simülasyonu üretir."
    )
    parser.add_argument("--input-csv", required=True, help="Kaggle CSV dosya yolu")
    parser.add_argument("--output-jsonl", default="output/simulated_telemetry.jsonl")
    parser.add_argument("--timestamp-col", default=None)
    parser.add_argument(
        "--channels",
        default=None,
        help=(
            "Opsiyonel virgulle ayrilmis kanal listesi. "
            "Verilmezse optimize edilmis sabit kanal listesi kullanilir."
        ),
    )
    parser.add_argument("--sampling-hz", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--event-coverage", type=float, default=0.02)
    parser.add_argument("--min-event-duration", type=int, default=1)
    parser.add_argument("--max-event-duration", type=int, default=4)
    parser.add_argument("--cooldown-sec", type=int, default=20)
    parser.add_argument("--row-offset", type=int, default=0)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument(
        "--output-format",
        choices=["jsonl", "json"],
        default="jsonl",
        help="Cikti dosya bicimi",
    )
    return parser.parse_args()


def resolve_channels(channels_arg: str | None) -> list[str]:
    if not channels_arg:
        return TARGET_CHANNELS.copy()

    requested = [c.strip() for c in channels_arg.split(",") if c.strip()]
    allowed = set(TARGET_CHANNELS)
    invalid = [c for c in requested if c not in allowed]
    if invalid:
        raise ValueError(
            "Bu pipeline yalnizca hedef kanal listesiyle calisir. "
            f"Gecersiz kanallar: {invalid}"
        )

    requested_set = set(requested)
    selected = [c for c in TARGET_CHANNELS if c in requested_set]
    if len(selected) < 3:
        raise ValueError("En az 3 gecerli hedef kanal verin.")
    return selected


def main() -> None:
    args = parse_args()
    channels = resolve_channels(args.channels)

    cfg = SimulationConfig(
        sampling_hz=args.sampling_hz,
        seed=args.seed,
        event_coverage=args.event_coverage,
        min_event_duration_sec=args.min_event_duration,
        max_event_duration_sec=args.max_event_duration,
        event_cooldown_sec=args.cooldown_sec,
    )

    prepared = load_and_prepare(
        input_csv=Path(args.input_csv),
        channels=channels,
        timestamp_col=args.timestamp_col,
        sampling_hz=cfg.sampling_hz,
        row_offset=args.row_offset,
        max_rows=args.max_rows,
    )

    simulated = simulate_dynamic_radiation(
        prepared=prepared,
        channels=channels,
        cfg=cfg,
    )
    records = to_jsonl_records(simulated, channels=channels)
    output_path = Path(args.output_jsonl)
    if args.output_format == "json":
        write_json(records, output_path)
    else:
        write_jsonl(records, output_path)

    summary = compute_summary(simulated)
    print("Simulasyon tamamlandi.")
    print(f"Cikti: {output_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
