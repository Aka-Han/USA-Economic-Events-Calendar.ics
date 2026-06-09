#!/usr/bin/env python3
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URLS = [
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json?version=1",
]

OUTPUT_FILE = Path("calendar.ics")

CALENDAR_NAME = "Live Economic Calendar - USD High Impact"
FF_URL = "https://www.forexfactory.com/calendar"
LOCATION = "Forex Factory"

# Forex Factory feed uses "country" as the currency code, e.g. "USD", "EUR", "JPY".
KEEP_CURRENCIES = {"USD"}

# Keep only high-impact events.
# If you want all USD events, change this to: set()
KEEP_IMPACTS = {"High"}

IMPORTANT_KEYWORDS = [
    "CPI", "Core CPI", "PPI", "Core PPI", "PCE", "Core PCE",
    "Non-Farm", "Nonfarm", "NFP", "Unemployment", "Average Hourly",
    "FOMC", "Federal Funds Rate", "Fed Interest Rate", "Powell",
    "GDP", "Advance GDP", "Prelim GDP", "Final GDP",
    "Retail Sales", "ISM", "JOLTS", "Jobless Claims",
    "Consumer Confidence", "PMI",
]

def fetch_json() -> list[dict]:
    last_error = None
    for url in SOURCE_URLS:
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 calendar-generator/1.0",
                    "Accept": "application/json,text/plain,*/*",
                },
            )
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            last_error = e
    raise RuntimeError(f"Could not fetch Forex Factory JSON: {last_error}")

def clean_text(value) -> str:
    return "" if value is None else str(value).strip()

def get_currency(item: dict) -> str:
    # Forex Factory JSON currently uses "country" for currency code.
    return clean_text(item.get("currency") or item.get("country")).upper()

def escape_ics(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", r"\n")
    )

def fold_ics_line(line: str) -> str:
    max_len = 73
    if len(line) <= max_len:
        return line
    parts = []
    while len(line) > max_len:
        parts.append(line[:max_len])
        line = " " + line[max_len:]
    parts.append(line)
    return "\r\n".join(parts)

def parse_datetime(item: dict) -> datetime | None:
    val = item.get("date") or item.get("datetime") or item.get("timestamp")
    if not val:
        return None

    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc)

    s = str(val).strip()

    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def get_impact(item: dict) -> str:
    impact = clean_text(item.get("impact") or item.get("importance"))
    low = impact.lower()
    if low in {"high impact expected", "red", "3"}:
        return "High"
    if low in {"medium impact expected", "orange", "2"}:
        return "Medium"
    if low in {"low impact expected", "yellow", "1"}:
        return "Low"
    return impact

def event_title(item: dict) -> str:
    title = (
        item.get("title")
        or item.get("event")
        or item.get("name")
        or item.get("headline")
        or "Forex Factory Event"
    )
    currency = get_currency(item)
    return f"{currency} {clean_text(title)}".strip()

def should_keep(item: dict) -> bool:
    currency = get_currency(item)
    impact = get_impact(item)

    if KEEP_CURRENCIES and currency not in KEEP_CURRENCIES:
        return False

    if KEEP_IMPACTS and impact not in KEEP_IMPACTS:
        title = event_title(item).lower()
        if not any(k.lower() in title for k in IMPORTANT_KEYWORDS):
            return False

    return True

def explain_event(title: str) -> str:
    t = title.lower()
    if "cpi" in t:
        return "通胀核心数据；高于预期通常推高美元和美债收益率，压制黄金/风险资产，具体取决于市场定价。"
    if "ppi" in t:
        return "上游价格压力数据；可能影响 CPI/PCE 预期。"
    if "pce" in t:
        return "Fed 更重视的通胀指标之一；Core PCE 对利率预期影响较大。"
    if "non-farm" in t or "nonfarm" in t or "nfp" in t or "unemployment" in t:
        return "劳动力市场核心数据；会影响美元、美债、黄金、股指。"
    if "fomc" in t or "federal funds" in t or "fed" in t:
        return "美联储政策事件；关注声明、点阵图、新闻发布会和市场预期差。"
    if "powell" in t:
        return "美联储主席讲话；可能影响政策路径预期。"
    if "gdp" in t:
        return "增长端核心数据；显著偏离预期会影响美元、收益率和指数。"
    if "retail sales" in t:
        return "消费强弱数据；美国消费韧性会影响增长与利率预期。"
    if "ism" in t or "pmi" in t:
        return "景气度数据；影响增长预期和风险偏好。"
    if "jolts" in t or "job openings" in t:
        return "职位空缺数据；衡量劳动力市场紧张程度。"
    if "jobless claims" in t:
        return "初请失业金；高频劳动力市场指标。"
    return "High impact macro event；实际影响取决于结果与市场预期差。"

def build_description(item: dict) -> str:
    title = event_title(item)
    forecast = clean_text(item.get("forecast")) or "Forex Factory 当天页面为准"
    previous = clean_text(item.get("previous")) or "Forex Factory 当天页面为准"
    actual = clean_text(item.get("actual")) or "未公布"
    currency = get_currency(item)
    impact = get_impact(item) or "High"

    return (
        f"Forecast: {forecast}\n"
        f"Previous: {previous}\n"
        f"Actual: {actual}\n"
        f"Currency: {currency}\n"
        f"Impact: {impact}\n"
        f"说明: {explain_event(title)}\n"
        f"备注: Forecast / Previous / Actual 会随 Forex Factory feed 更新；交易前请打开 URL 复核。"
    )

def create_ics(events: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LiveEconomicCalendar//ForexFactory//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_ics(CALENDAR_NAME)}",
        "X-WR-TIMEZONE:UTC",
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
        "X-PUBLISHED-TTL:PT6H",
    ]

    seen = set()
    kept_count = 0

    for item in events:
        if not should_keep(item):
            continue

        start_dt = parse_datetime(item)
        if not start_dt:
            continue

        title = event_title(item)
        key = (start_dt.isoformat(), title)
        if key in seen:
            continue
        seen.add(key)

        kept_count += 1
        end_dt = start_dt + timedelta(minutes=30)
        uid_seed = f"{start_dt.isoformat()}-{title}"
        uid = f"{uuid.uuid5(uuid.NAMESPACE_URL, uid_seed)}@live-economic-calendar"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now}",
            f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{escape_ics(title)}",
            f"DESCRIPTION:{escape_ics(build_description(item))}",
            f"LOCATION:{escape_ics(LOCATION)}",
            f"URL:{FF_URL}",
            "BEGIN:VALARM",
            "TRIGGER:-PT30M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{escape_ics('30分钟后: ' + title)}",
            "END:VALARM",
            "BEGIN:VALARM",
            "TRIGGER:-PT5M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{escape_ics('5分钟后: ' + title)}",
            "END:VALARM",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    print(f"Kept events: {kept_count}")
    return "\r\n".join(fold_ics_line(line) for line in lines) + "\r\n"

def main() -> int:
    data = fetch_json()
    ics = create_ics(data)
    OUTPUT_FILE.write_text(ics, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE.resolve()}")
    print(f"Events in source: {len(data)}")
    print(f"ICS size: {len(ics)} chars")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
