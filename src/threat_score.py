"""
src/threat_score.py
Safe threat scoring module.
✔ Prevents 'int has no attribute fillna'
✔ Robust to missing columns
✔ Works with single-row df
"""

import pandas as pd
import numpy as np

# weights
W_RF = 0.30
W_ISO = 0.30
W_SIGNATURE = 0.25
W_ENTROPY = 0.10
W_PAYLOAD = 0.05


def _ensure_series(value):
    """Convert scalar to 1-row Series → prevents fillna() crash."""
    if isinstance(value, pd.Series):
        return value
    return pd.Series([value])


def _norm(series, eps=1e-6):
    series = _ensure_series(series).astype(float).fillna(0)
    mn, mx = series.min(), series.max()
    return (series - mn) / ((mx - mn) + eps)


def compute_threat_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # strict casting
    df["RF_Prediction"] = _ensure_series(df.get("RF_Prediction", 0)).astype(int)
    df["ISO_Prediction"] = _ensure_series(df.get("ISO_Prediction", 0)).astype(int)

    df["Attack_Type"] = df.get("Attack_Type", None)

    df["url_entropy"] = _ensure_series(df.get("url_entropy", 0)).astype(float)
    df["payload_length"] = _ensure_series(df.get("payload_length", 0)).astype(float)

    # signature flag
    sig = df["Attack_Type"].notna().astype(int)

    # normalize
    ent_norm = _norm(df["url_entropy"])
    payload_norm = _norm(df["payload_length"])

    score_cont = (
        W_RF * df["RF_Prediction"]
        + W_ISO * df["ISO_Prediction"]
        + W_SIGNATURE * sig
        + W_ENTROPY * ent_norm
        + W_PAYLOAD * payload_norm
    )

    df["Threat_Score"] = (score_cont.clip(0, 1) * 100).round(1)

    def level(v):
        if v >= 70: return "High"
        if v >= 35: return "Medium"
        return "Low"

    df["Threat_Level"] = df["Threat_Score"].apply(level)

    return df
