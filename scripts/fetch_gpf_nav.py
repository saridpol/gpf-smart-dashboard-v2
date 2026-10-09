import json
import re
import urllib.request
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path

URL = "https://www.gpf.or.th/thai2019/about/main.php?lang=th&menu=statistic&page=memberfund&pattern=n&size=n"
OUTPUT = Path("nav-data.json")
MAX_AGE_DAYS = 10
KEYS = ("shariah", "agg35", "agg65", "foreign")


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        value = " ".join((data or "").split())
        if value:
            self.parts.append(value)


def to_date(raw):
    day, month, year = map(int, raw.split("/"))
    if year >= 2400:
        year -= 543
    return date(year, month, day)


def read_existing():
    try:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        nav = data.get("nav", {})
        if data.get("date") and all(isinstance(nav.get(k), (int, float)) and not isinstance(nav.get(k), bool) and nav[k] > 0 for k in KEYS):
            return data
    except (OSError, ValueError, AttributeError, TypeError):
        pass
    return None


def write(data):
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fallback(reason):
    data = read_existing()
    if data is None:
        raise SystemExit("Fetch failed and no valid fallback exists: " + str(reason))
    data["verified"] = False
    data["status"] = "fallback_latest_available"
    data["status_message"] = "ดึง NAV ใหม่ไม่ได้ จึงคงข้อมูลสำรองเดิมไว้; โปรดตรวจวันที่ก่อนใช้อ้างอิง"
    data["last_fetch_attempt"] = datetime.now().astimezone().isoformat(timespec="seconds")
    data["fetch_error"] = str(reason)[:500]
    write(data)
    print("Fallback retained; existing date and NAV values were preserved.")
    print(json.dumps({"date": data["date"], "nav": data["nav"], "status": data["status"], "fetch_error": data["fetch_error"]}, ensure_ascii=False))


def main():
    try:
        req = urllib.request.Request(URL, headers={
            "User-Agent": "Mozilla/5.0 (compatible; GPFNAVUpdater/2.0)",
            "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8", "replace")
        parser = TextParser()
        parser.feed(html)
        text = re.sub(r"\s+", " ", " | ".join(parser.parts))
        if any(x in text.lower() for x in ("maintenance", "temporarily unavailable", "ปิดปรับปรุง", "อยู่ระหว่างปรับปรุง")):
            fallback("Official page appears to be under maintenance.")
            return
        dates = []
        for raw in re.findall(r"(?<!\d)(\d{1,2}/\d{1,2}/(?:25\d{2}|20\d{2}))(?!\d)", text):
            try:
                dates.append((to_date(raw), raw))
            except ValueError:
                continue
        if not dates:
            fallback("Could not find a valid NAV date in the official page text.")
            return
        patterns = {
            "shariah": r"(?:แผนการลงทุนตามหลัก\s*ชะรีอะฮ์|ชะรีอะฮ์|ชารีอะฮ์|Shariah).{0,220}?(\d{1,3}\.\d{4})",
            "agg35": r"(?:แผนเชิงรุก\s*35|เชิงรุก\s*35|Aggressive\s*35).{0,220}?(\d{1,3}\.\d{4})",
            "agg65": r"(?:แผนเชิงรุก\s*65|เชิงรุก\s*65|Aggressive\s*65).{0,220}?(\d{1,3}\.\d{4})",
            "foreign": r"(?:แผนหุ้นต่างประเทศ|หุ้นต่างประเทศ|Foreign Equity).{0,220}?(\d{1,3}\.\d{4})",
        }
        nav = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                fallback(f"Could not reliably locate {key} NAV beside its plan label.")
                return
            nav[key] = float(match.group(1))
        nav_date, raw_date = max(dates, key=lambda item: item[0])
        age = (datetime.now().date() - nav_date).days
        if age < 0 or age > MAX_AGE_DAYS:
            fallback(f"Page date {raw_date} is outside allowed freshness window ({age} days).")
            return
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        data = {
            "date": f"{nav_date.day}/{nav_date.month}/{nav_date.year + 543}",
            "nav_date_iso": nav_date.isoformat(),
            "nav": nav,
            "source": URL,
            "fetched_at": now,
            "last_fetch_attempt": now,
            "verified": True,
            "status": "official_page_parsed",
            "status_message": "พบวันที่และ NAV ครบทั้ง 4 แผนจากหน้า กบข.; ควรตรวจสอบผลการจับคู่กับหน้าเว็บจริง",
        }
        write(data)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as exc:
        fallback(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
