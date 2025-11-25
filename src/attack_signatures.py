"""
src/attack_signatures.py
Robust attack signature detection (SQLi, XSS, Traversal, Bots).
Fully safe for empty or missing values.
"""

import re
import pandas as pd

# Patterns
SQL_PATTERNS = [
    r"(\bor\b\s+\d+=\d+)", r"union(\s+all)?\s+select", r"select.+from", r"insert\s+into",
    r"drop\s+table", r"--", r"'\s*or\s*'", r"or\s+1=1", r"sleep\(", r"benchmark\("
]
XSS_PATTERNS = [
    r"<script\b", r"javascript:", r"onerror\s*=", r"onload\s*=", r"<img\s+.*onerror",
    r"<iframe\b", r"%3Cscript%3E"
]
TRAVERSAL_PATTERNS = [r"\.\./", r"\.\.\\", r"etc/passwd", r"/proc/", r"\\windows\\"]

BOT_UA_KEYWORDS = ["bot", "crawl", "spider", "slurp", "curl", "wget", "python-requests"]

_sql_re = re.compile("|".join(SQL_PATTERNS), re.IGNORECASE)
_xss_re = re.compile("|".join(XSS_PATTERNS), re.IGNORECASE)
_trav_re = re.compile("|".join(TRAVERSAL_PATTERNS), re.IGNORECASE)


def detect_sqli(text: str) -> bool:
    text = str(text or "")
    return bool(_sql_re.search(text))


def detect_xss(text: str) -> bool:
    text = str(text or "")
    return bool(_xss_re.search(text))


def detect_traversal(text: str) -> bool:
    text = str(text or "")
    return bool(_trav_re.search(text))


def detect_bot(user_agent: str) -> bool:
    ua = str(user_agent or "").lower()
    return any(k in ua for k in BOT_UA_KEYWORDS)


def detect_attack_type(url="", body="", user_agent=""):
    combined = f"{url} {body}".lower()
    if detect_sqli(combined): return "SQLi"
    if detect_xss(combined): return "XSS"
    if detect_traversal(combined): return "Traversal"
    if detect_bot(user_agent): return "Bot"
    return None


def annotate_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["url"] = df.get("url", "").fillna("").astype(str)
    df["body"] = df.get("body", "").fillna("").astype(str)
    df["user_agent"] = df.get("user_agent", "").fillna("").astype(str)

    df["Attack_Type"] = df.apply(
        lambda r: detect_attack_type(r["url"], r["body"], r["user_agent"]),
        axis=1
    )
    return df
