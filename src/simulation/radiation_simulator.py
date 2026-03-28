#bu dosya radyasyon simülasyonu üretmek için temel fonksiyonları içerir. 


from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SimulationConfig:
    sampling_hz: int = 1
    seed: int = 42
    event_coverage: float = 0.02
    min_event_duration_sec: int = 1
    max_event_duration_sec: int = 4
    event_cooldown_sec: int = 20
    baseline_radiation_mean: float = 0.03
    baseline_radiation_std: float = 0.01


SEVERITY_LEVELS: Tuple[str, ...] = ("low", "medium", "high")
SEVERITY_WEIGHTS = np.array([0.60, 0.30, 0.10], dtype=float)
SEVERITY_RADIATION_MULTIPLIER = {
    "low": (2.0, 3.0),
    "medium": (4.0, 6.0),
    "high": (7.0, 10.0),
}

EVENT_TYPES: Tuple[str, ...] = ("spike", "bit_flip_like")
EVENT_TYPE_WEIGHTS = np.array([0.70, 0.30], dtype=float)


def _normalize_weights(weights: np.ndarray) -> np.ndarray:
    total = float(weights.sum())
    if total <= 0.0:
        raise ValueError("Weights must sum to a positive number.")
    return weights / total


def _select_timestamp_column(df: pd.DataFrame, timestamp_col: Optional[str]) -> str:
    if timestamp_col and timestamp_col in df.columns:
        return timestamp_col

    candidates = ["timestamp", "time", "datetime", "date"]
    for name in candidates:
        if name in df.columns:
            return name

    raise ValueError(
        "Timestamp column not found. Pass --timestamp-col explicitly or include one of: "
        "timestamp, time, datetime, date"
    )


def load_and_prepare(
    input_csv: Path,
    channels: Iterable[str],
    timestamp_col: Optional[str],
    sampling_hz: int,
    row_offset: int = 0,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    if row_offset < 0:
        raise ValueError("row_offset 0 veya daha buyuk olmalidir.")

    header_df = pd.read_csv(input_csv, nrows=0)
    ts_col = _select_timestamp_column(header_df, timestamp_col)

    channels = list(channels)
    missing = [col for col in channels if col not in header_df.columns]
    if missing:
        raise ValueError(f"Missing channels in input data: {missing}")

    usecols = [ts_col, *channels]
    skiprows = range(1, row_offset + 1) if row_offset > 0 else None
    nrows = max_rows if max_rows is not None and max_rows > 0 else None

    df = pd.read_csv(
        input_csv,
        usecols=usecols,
        skiprows=skiprows,
        nrows=nrows,
    )

    work = df[[ts_col, *channels]].copy()
    work[ts_col] = pd.to_datetime(work[ts_col], errors="coerce", utc=True)
    work = work.dropna(subset=[ts_col]).sort_values(ts_col)
    work = work.set_index(ts_col)

    for col in channels:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    # 1 Hz standardization via resample + interpolation.
    freq = f"{int(round(1 / sampling_hz if sampling_hz > 1 else 1))}s" if sampling_hz != 1 else "1s"
    if sampling_hz != 1:
        # For non-1Hz, prefer exact seconds per sample.
        period_seconds = max(1, int(round(1 / sampling_hz)))
        freq = f"{period_seconds}s"

    resampled = work.resample(freq).mean().interpolate(method="time").ffill().bfill()
    resampled.index.name = "timestamp"
    return resampled


def _build_channel_bounds(df: pd.DataFrame, channels: List[str]) -> Dict[str, Tuple[float, float]]:
    bounds: Dict[str, Tuple[float, float]] = {}
    for col in channels:
        q1, q99 = np.nanpercentile(df[col].to_numpy(dtype=float), [1, 99])
        span = max(1e-9, q99 - q1)
        bounds[col] = (float(q1 - 0.2 * span), float(q99 + 0.2 * span))
    return bounds


def _sample_event_windows(
    n: int,
    cfg: SimulationConfig,
    rng: np.random.Generator,
) -> List[Tuple[int, int]]:
    target_samples = max(1, int(n * cfg.event_coverage))
    windows: List[Tuple[int, int]] = []
    covered = np.zeros(n, dtype=bool)

    attempts = 0
    max_attempts = n * 5
    while covered.sum() < target_samples and attempts < max_attempts:
        attempts += 1
        dur = int(rng.integers(cfg.min_event_duration_sec, cfg.max_event_duration_sec + 1))
        if dur <= 0 or dur >= n:
            continue
        start = int(rng.integers(0, n - dur))
        end = start + dur

        left = max(0, start - cfg.event_cooldown_sec)
        right = min(n, end + cfg.event_cooldown_sec)
        if covered[left:right].any():
            continue

        windows.append((start, end))
        covered[start:end] = True

    windows.sort(key=lambda x: x[0])
    return windows


def _apply_event_effect(
    value: float,
    event_type: str,
    severity: str,
    sigma: float,
    rng: np.random.Generator,
) -> float:
    if event_type == "spike":
        scale = {"low": 2.5, "medium": 3.5, "high": 5.0}[severity]
        return value + float(rng.normal(scale * sigma, 0.25 * sigma))
    if event_type == "drop":
        scale = {"low": 2.0, "medium": 3.0, "high": 4.5}[severity]
        return value - float(abs(rng.normal(scale * sigma, 0.3 * sigma)))

    # bit_flip_like: sign/bit-like perturbation with bounded extreme jump.
    jump_factor = {"low": 0.05, "medium": 0.12, "high": 0.20}[severity]
    sign = -1.0 if rng.random() < 0.5 else 1.0
    return value + sign * (abs(value) * jump_factor + float(rng.normal(0, sigma)))


def simulate_dynamic_radiation(
    prepared: pd.DataFrame,
    channels: List[str],
    cfg: SimulationConfig,
) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    n = len(prepared)
    if n < 10:
        raise ValueError("Input after preprocessing is too short; need at least 10 rows.")

    noisy = prepared[channels].copy()
    clean = prepared[channels].copy()
    bounds = _build_channel_bounds(prepared, channels)
    windows = _sample_event_windows(n, cfg, rng)

    severity_probs = _normalize_weights(SEVERITY_WEIGHTS)
    event_probs = _normalize_weights(EVENT_TYPE_WEIGHTS)

    is_event = np.zeros(n, dtype=bool)
    event_type_arr = np.array(["none"] * n, dtype=object)
    severity_arr = np.array(["none"] * n, dtype=object)
    event_id_arr = np.array([""] * n, dtype=object)
    # Use a regular Python list for affected channels to avoid numpy broadcasting issues
    affected_channels_list = [[] for _ in range(n)]

    baseline = np.clip(
        rng.normal(cfg.baseline_radiation_mean, cfg.baseline_radiation_std, size=n),
        0.0,
        None,
    )
    radiation = baseline.copy()

    channel_sigma = {
        col: max(1e-9, float(np.nanstd(clean[col].to_numpy(dtype=float)))) for col in channels
    }

    event_counter = 0
    for start, end in windows:
        event_counter += 1
        event_id = f"evt_{event_counter:03d}"
        event_type = str(rng.choice(EVENT_TYPES, p=event_probs))
        severity = str(rng.choice(SEVERITY_LEVELS, p=severity_probs))
        mult_min, mult_max = SEVERITY_RADIATION_MULTIPLIER[severity]

        for i in range(start, end):
            is_event[i] = True
            event_type_arr[i] = event_type
            severity_arr[i] = severity
            event_id_arr[i] = event_id

            radiation[i] = baseline[i] * float(rng.uniform(mult_min, mult_max))

            affected = []
            for col in channels:
                base_value = float(clean.iloc[i][col])
                sigma = channel_sigma[col]
                changed = _apply_event_effect(base_value, event_type, severity, sigma, rng)
                lo, hi = bounds[col]
                clipped = float(np.clip(changed, lo, hi))
                noisy.iat[i, noisy.columns.get_loc(col)] = clipped
                
                # Sadece değişen kanalları kaydet
                if abs(clipped - base_value) > 1e-9:
                    affected.append(col)
            
            affected_channels_list[i] = affected

    out = pd.DataFrame(index=prepared.index)
    out["radiation_level"] = radiation
    out["is_radiation_event"] = is_event
    out["event_type"] = event_type_arr
    out["severity"] = severity_arr
    out["event_id"] = event_id_arr
    out["affected_channels"] = affected_channels_list

    for col in channels:
        out[f"clean__{col}"] = clean[col].to_numpy(dtype=float)
        out[f"noisy__{col}"] = noisy[col].to_numpy(dtype=float)

    return out


def to_jsonl_records(simulated: pd.DataFrame, channels: List[str]) -> List[dict]:
    records: List[dict] = []
    for ts, row in simulated.iterrows():
        clean_vals = {col: float(row[f"clean__{col}"]) for col in channels}
        noisy_vals = {col: float(row[f"noisy__{col}"]) for col in channels}
        
        is_radiation_event = bool(row["is_radiation_event"])
        
        labels = {
            "is_radiation_event": is_radiation_event,
            "event_type": str(row["event_type"]),
            "severity": str(row["severity"]),
        }

        # Base record
        rec = {
            "timestamp": pd.Timestamp(ts).isoformat(),
            "channels": {
                "clean": clean_vals,
                "noisy": noisy_vals,
            },
            "labels": labels,
        }
        
        # Tüm kanal değerleri (kirlenmiş)
        for col in channels:
            rec[col] = noisy_vals[col]
        
        # Radyasyon eventi varsa, detaylı bilgi ve orijinal değerler
        if is_radiation_event:
            affected = row.get("affected_channels", [])
            if not isinstance(affected, list):
                affected = list(affected) if hasattr(affected, '__iter__') else []
            
            rec["radiation_event"] = {
                "event_id": str(row.get("event_id", "")),
                "event_type": str(row["event_type"]),
                "severity": str(row["severity"]),
                "affected_channels": affected,
            }
            
            # Orijinal değerleri ekle (sadece etkilenen kanallar için)
            for col in affected:
                rec[f"{col}_original"] = clean_vals[col]
        
        records.append(rec)
    
    return records


def write_jsonl(records: List[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def write_json(records: List[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)


def compute_summary(simulated: pd.DataFrame) -> dict:
    total = len(simulated)
    event_count = int(simulated["is_radiation_event"].sum())
    coverage = event_count / total if total else 0.0
    by_type = simulated.loc[simulated["is_radiation_event"], "event_type"].value_counts().to_dict()
    by_severity = simulated.loc[simulated["is_radiation_event"], "severity"].value_counts().to_dict()
    return {
        "total_samples": total,
        "event_samples": event_count,
        "event_coverage": coverage,
        "event_type_counts": by_type,
        "severity_counts": by_severity,
    }
