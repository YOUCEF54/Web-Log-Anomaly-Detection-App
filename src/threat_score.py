# src/threat_score.py
import pandas as pd
import numpy as np

# weights (tunable)
W_RF = 0.30
W_ISO = 0.30
W_SIGNATURE = 0.25
W_ENTROPY = 0.10
W_PAYLOAD = 0.05


def _norm(series, eps=1e-6):
    if series.empty:
        return series
    mn = series.min()
    mx = series.max()
    denom = (mx - mn) + eps
    return (series - mn) / denom


def compute_threat_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expects df to have: RF_Prediction (0/1), ISO_Prediction (0/1), Attack_Type, url_entropy, payload_length
    Returns df with Threat_Score and Threat_Level
    """
    df = df.copy()

    df["RF_Prediction"] = df.get("RF_Prediction", 0).fillna(0).astype(int)
    df["ISO_Prediction"] = df.get("ISO_Prediction", 0).fillna(0).astype(int)
    df["Attack_Type"] = df.get("Attack_Type", None)
    df["url_entropy"] = df.get("url_entropy", 0).fillna(0).astype(float)
    df["payload_length"] = df.get("payload_length", 0).fillna(0).astype(float)

    df["signature_flag"] = (~df["Attack_Type"].isna()) & (df["Attack_Type"] != "")
    sig = df["signature_flag"].astype(int)

    ent_norm = _norm(df["url_entropy"])
    payload_norm = _norm(df["payload_length"])

    score_cont = (W_RF * df["RF_Prediction"]
                  + W_ISO * df["ISO_Prediction"]
                  + W_SIGNATURE * sig
                  + W_ENTROPY * ent_norm
                  + W_PAYLOAD * payload_norm)

    df["Threat_Score"] = (score_cont.clip(0, 1) * 100).round(1)

    def level(s):
        if s >= 70:
            return "High"
        if s >= 35:
            return "Medium"
        return "Low"

    df["Threat_Level"] = df["Threat_Score"].apply(level)

    df.drop(columns=["signature_flag"], inplace=True, errors="ignore")
    return df
