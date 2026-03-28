#bu dosya ESA Mission kanal pickle dosyalarini tek flat CSV dosyasina cevirir.
#Bu, run_simulation.py gibi diger scriptlerin tek bir CSV uzerinden calismasini kolaylastirir.

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import pandas as pd


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
        description="ESA Mission kanal pickle dosyalarini tek flat CSV dosyasina cevirir."
    )
    parser.add_argument(
        "--mission-root",
        required=True,
        help="Mission kok yolu. Ornek: data/raw/ESA-Mission1/ESA-Mission1",
    )
    parser.add_argument(
        "--channels",
        default=None,
        help=(
            "Opsiyonel virgulle ayrilmis kanal listesi. "
            "Verilmezse optimize edilmis sabit kanal listesi kullanilir."
        ),
    )
    parser.add_argument(
        "--output-csv",
        default="data/processed/telemetry_flat.csv",
        help="Uretilecek flat CSV yolu.",
    )
    parser.add_argument(
        "--join",
        choices=("outer", "inner"),
        default="outer",
        help="Kanal birlestirme tipi. outer daha guvenli, inner daha kucuk olabilir.",
    )
    parser.add_argument(
        "--start",
        default=None,
        help="Opsiyonel baslangic zamani. Ornek: 2000-01-01T00:00:00Z",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Opsiyonel bitis zamani. Ornek: 2000-01-03T00:00:00Z",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Opsiyonel satir limiti (head). Hizli test icin yararli.",
    )
    return parser.parse_args()


def _parse_channels(channels_arg: str) -> List[str]:
    channels = [c.strip() for c in channels_arg.split(",") if c.strip()]
    if len(channels) < 3:
        raise ValueError("En az 3 kanal vermen gerekiyor.")
    return channels


def resolve_channels(channels_arg: str | None) -> List[str]:
    if not channels_arg:
        return TARGET_CHANNELS.copy()

    requested = _parse_channels(channels_arg)
    allowed = set(TARGET_CHANNELS)
    invalid = [c for c in requested if c not in allowed]
    if invalid:
        raise ValueError(
            "Bu donusturucu yalnizca hedef kanal listesiyle calisir. "
            f"Gecersiz kanallar: {invalid}"
        )

    requested_set = set(requested)
    selected = [c for c in TARGET_CHANNELS if c in requested_set]
    if len(selected) < 3:
        raise ValueError("En az 3 gecerli hedef kanal verin.")
    return selected


def _read_channel_df(mission_root: Path, channel_name: str) -> pd.DataFrame:
    channel_file = mission_root / "channels" / channel_name / channel_name
    if not channel_file.exists():
        raise FileNotFoundError(f"Kanal dosyasi bulunamadi: {channel_file}")

    df = pd.read_pickle(channel_file)
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Beklenmeyen veri tipi ({channel_name}): {type(df)}")

    # Baz dosyalarda kolon ismi farkli olabilecegi icin tek kolonu kanal ismine sabitliyoruz.
    if df.shape[1] != 1:
        raise ValueError(f"{channel_name} tek kolonlu degil: kolon sayisi={df.shape[1]}")

    out = df.copy()
    out.columns = [channel_name]
    out.index = pd.to_datetime(out.index, errors="coerce")
    out = out[~out.index.isna()].sort_index()
    out[channel_name] = pd.to_numeric(out[channel_name], errors="coerce")
    return out


def _merge_channels(channel_dfs: Iterable[pd.DataFrame], join_type: str) -> pd.DataFrame:
    merged = pd.concat(list(channel_dfs), axis=1, join=join_type, sort=False)
    merged = merged.sort_index()
    merged.index.name = "timestamp"
    return merged


def main() -> None:
    args = parse_args()
    mission_root = Path(args.mission_root)
    if not mission_root.exists():
        raise FileNotFoundError(f"Mission root bulunamadi: {mission_root}")

    channels = resolve_channels(args.channels)
    channel_dfs = [_read_channel_df(mission_root, channel) for channel in channels]
    merged = _merge_channels(channel_dfs, join_type=args.join)

    if args.start:
        start_ts = pd.to_datetime(args.start, errors="raise")
        merged = merged.loc[merged.index >= start_ts]
    if args.end:
        end_ts = pd.to_datetime(args.end, errors="raise")
        merged = merged.loc[merged.index <= end_ts]

    if args.max_rows is not None and args.max_rows > 0:
        merged = merged.head(args.max_rows)

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=True)

    print("Donusum tamamlandi.")
    print(f"Cikti: {output_path}")
    print(f"Satir: {len(merged)}")
    print(f"Kanal sayisi: {len(channels)}")
    print(f"Kolonlar: {', '.join(['timestamp', *channels])}")


if __name__ == "__main__":
    main()
