# src/parse_logs.py
"""
Parsing for CSIC2010 raw text files and Apache access.log lines.

Outputs a CSV at ../data/csic_database.csv when executed as main.
"""

import os
import re
import pandas as pd
from typing import List
import sys 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import CSIC_DIR, CSIC_CSV


# Regex to split HTTP request blocks (flexible)
BLOCK_SPLIT_REGEX = re.compile(r"\r?\n\s*\r?\n")

def parse_request_block(block: str):
    block = block.strip()
    if not block:
        return None

    lines = block.splitlines()
    first = lines[0].strip() if lines else ""
    method = url = protocol = ""

    m = re.match(r"(GET|POST|HEAD|PUT|DELETE|OPTIONS|TRACE)\s+(\S+)\s+(.*)", first, flags=re.IGNORECASE)
    if m:
        method = m.group(1).upper()
        url = m.group(2)
        protocol = m.group(3)
    headers = {"Host": "", "User-Agent": "", "Cookie": "", "Content-Type": "", "Content-Length": ""}
    body_lines = []
    header_section = True

    for line in lines[1:]:
        if header_section and line.strip() == "":
            header_section = False
            continue
        if header_section and ":" in line:
            try:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in headers:
                    headers[key] = val
            except Exception:
                continue
            continue
        if not header_section:
            if line.strip():
                body_lines.append(line.strip())

    body = "&".join(body_lines)
    return {
        "method": method,
        "url": url,
        "protocol": protocol,
        "host": headers["Host"],
        "user_agent": headers["User-Agent"],
        "cookie": headers["Cookie"],
        "content_type": headers["Content-Type"],
        "content_length": headers["Content-Length"],
        "body": body
    }

# Apache/Nginx combined log regex
APACHE_LOG_REGEX = re.compile(
    r'(?P<ip>\S+) '            # IP
    r'\S+ \S+ '                # ident / user
    r'\[(?P<timestamp>.*?)\] ' # timestamp
    r'"(?P<method>\S+)? (?P<url>\S+)? (?P<protocol>[^"]+)?" '  # request
    r'(?P<status>\d{3}) '      # status
    r'(?P<size>\S+) '          # size
    r'"(?P<referrer>[^"]*)" '  # referrer
    r'"(?P<user_agent>[^"]*)"' # user agent
)

def parse_apache_log_lines(lines: List[str]) -> pd.DataFrame:
    rows = []
    for line in lines:
        try:
            m = APACHE_LOG_REGEX.match(line)
            if not m:
                continue
            d = m.groupdict()
            rows.append({
                "method": d.get("method", "") or "",
                "url": d.get("url", "") or "",
                "protocol": d.get("protocol", "") or "",
                "status": d.get("status", "") or "",
                "content_length": d.get("size", "") or "0",
                "user_agent": d.get("user_agent", "") or "",
                "cookie": "",
                "content_type": "",
                "body": ""
            })
        except Exception:
            continue
    return pd.DataFrame(rows)

def parse_file(filename: str, label: int):
    filepath = os.path.join(CSIC_DIR, filename)
    print(f"Parsing {filepath} ...")
    with open(filepath, "r", encoding="latin-1", errors="ignore") as f:
        content = f.read()
    blocks = re.split(BLOCK_SPLIT_REGEX, content)
    rows = []
    for b in blocks:
        try:
            parsed = parse_request_block(b)
            if parsed:
                parsed["label"] = int(label)
                rows.append(parsed)
        except Exception:
            continue
    print(f"Parsed {len(rows)} requests from {filename}")
    return rows

def build_csv(output_path=CSIC_CSV):
    all_rows = []
    # filenames expected in csic_2010/
    files = [
        ("normalTrafficTraining.txt", 0),
        ("normalTrafficTest.txt", 0),
        ("anomalousTrafficTest.txt", 1),
    ]
    for fname, lab in files:
        path = os.path.join(CSIC_DIR, fname)
        if os.path.exists(path):
            all_rows += parse_file(fname, lab)
        else:
            print(f"Warning: {path} not found (skipped).")
    df = pd.DataFrame(all_rows)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Saved dataset to: {output_path} (rows={len(df)})")
    return df

if __name__ == "__main__":
    os.makedirs(os.path.dirname(CSIC_CSV), exist_ok=True)
    build_csv()
