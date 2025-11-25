"""
scripts/generate_sample_log.py
Generates a sample Apache-like access.log with 100 lines mixing normal requests, SQLi, XSS, bots.
Saves to data/sample_access.log
"""
import random
import os

OUT = os.path.join("data", "sample_access.log")
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0",
    "curl/7.68.0",
    "Googlebot/2.1 (+http://www.google.com/bot.html)",
    "python-requests/2.31.0",
    "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)"
]

URL_NORMAL = [
    "/index.html", "/products", "/login", "/cart?id=3", "/search?q=wine"
]

SQLI = [
    "/search?q=1' OR '1'='1", "/product?id=3 UNION SELECT username,password FROM users", "/login?user=admin'--"
]

XSS = [
    "/search?q=<script>alert(1)</script>", "/comment?c=<img src=x onerror=alert(1)>"
]

TRAV = [
    "/download?file=../../../../etc/passwd", "/view?path=..\\..\\windows\\system32\\drivers\\etc\\hosts"
]

def gen_line(ip, ts, method, url, protocol, status, size, referrer, ua):
    # Common Log Format like:
    # 127.0.0.1 - - [01/Jan/2025:12:00:00 +0000] "GET /index.html HTTP/1.1" 200 123 "-" "UA"
    return f'{ip} - - [{ts}] "{method} {url} {protocol}" {status} {size} "{referrer}" "{ua}"\n'

def random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def random_ts():
    # simplified timestamp
    return "01/Jan/2025:12:00:00 +0000"

def main(n=100, out=OUT):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lines = []
    for i in range(n):
        ip = random_ip()
        ts = random_ts()
        method = random.choice(["GET", "POST"])
        r = random.random()
        if r < 0.65:
            url = random.choice(URL_NORMAL)
            status = random.choice([200, 200, 200, 302])
        elif r < 0.80:
            url = random.choice(SQLI)
            status = random.choice([200, 500, 400])
        elif r < 0.90:
            url = random.choice(XSS)
            status = random.choice([200, 400])
        else:
            url = random.choice(TRAV)
            status = random.choice([200, 404, 403])
        size = random.randint(40, 4000)
        referrer = "-"
        ua = random.choice(USER_AGENTS)
        protocol = "HTTP/1.1"
        lines.append(gen_line(ip, ts, method, url, protocol, status, size, referrer, ua))

    with open(out, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Generated {n} lines → {out}")

if __name__ == "__main__":
    main()
