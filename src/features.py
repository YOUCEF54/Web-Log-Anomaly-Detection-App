# src/features.py
"""
Simplified feature extractor (7 features) — robust to NaN
"""
import pandas as pd
import math
from collections import Counter
import re

SQL_KEYWORDS = ["select", "union", "insert", "drop", "--", "'", '"', "or 1=1"]

def entropy(text: str) -> float:
    if not text:
        return 0.0
    freq = Counter(text)
    L = len(text)
    return -sum((c / L) * math.log2(c / L) for c in freq.values())

def build_features(df: pd.DataFrame):
    """
    Input: DataFrame containing columns like 'url', 'method', 'body', 'user_agent', ...
    Output: (X_df, feature_cols)
    """
    df = df.copy()

    # ensure required columns exist
    for col in ["url", "method", "body", "user_agent", "cookie", "content_type", "content_length", "accept"]:
        if col not in df.columns:
            df[col] = ""

    # normalize types
    df["url"] = df["url"].fillna("").astype(str)
    df["method"] = df["method"].fillna("").astype(str)
    df["body"] = df["body"].fillna("").astype(str)
    df["user_agent"] = df["user_agent"].fillna("").astype(str)
    df["cookie"] = df["cookie"].fillna("").astype(str)
    df["content_type"] = df["content_type"].fillna("").astype(str)
    df["content_length"] = df["content_length"].fillna("0").astype(str)
    df["accept"] = df["accept"].fillna("").astype(str)

    # Simplified 7 features
    df["url_length"] = df["url"].apply(len)
    df["param_count"] = df["url"].str.count("&").fillna(0).astype(int)
    df["has_special_chars"] = df["url"].str.contains(r"[<>'\"%;()]", regex=True, na=False).astype(int)
    df["has_sql"] = df["url"].str.lower().apply(lambda x: int(any(k in x for k in SQL_KEYWORDS)))
    df["method_encoded"] = df["method"].map({"GET": 0, "POST": 1}).fillna(0).astype(int)
    df["payload_length"] = df["body"].apply(lambda x: len(str(x)))
    df["url_entropy"] = df["url"].apply(lambda x: entropy(str(x)))

    feature_cols = [
        "url_length",
        "param_count",
        "has_special_chars",
        "has_sql",
        "method_encoded",
        "payload_length",
        "url_entropy"
    ]

    X = df[feature_cols].copy()
    # ensure numeric dtype
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

    return X, feature_cols
