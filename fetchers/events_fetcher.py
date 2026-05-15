"""
Vietnam Events Fetcher
=================================
從 RSS 和 Google News 取得胡志明市與河內近期活動資訊，
供 AI 播報「生活情報」區段使用。
"""

import feedparser
from datetime import datetime, timezone, timedelta
import pytz
import time

HCMC_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


def _is_today_or_upcoming(entry, days_ahead=3):
    now_hcmc = datetime.now(HCMC_TZ)
    cutoff_past   = now_hcmc - timedelta(hours=12)
    cutoff_future = now_hcmc + timedelta(days=days_ahead)

    for attr in ('published_parsed', 'updated_parsed'):
        t = getattr(entry, attr, None)
        if t is None:
            continue
        try:
            dt_utc  = datetime(*t[:6], tzinfo=timezone.utc)
            dt_hcmc = dt_utc.astimezone(HCMC_TZ)
            return cutoff_past <= dt_hcmc <= cutoff_future
        except Exception:
            continue
    return True


def _parse_feed(url, limit=4, label=""):
    events = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if len(events) >= limit:
                break
            if not _is_today_or_upcoming(entry):
                continue
            title   = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            link    = entry.get("link", "")
            if not title:
                continue
            events.append({
                "title":   title,
                "summary": summary[:200] if summary else "",
                "link":    link,
                "source":  label,
            })
    except Exception as e:
        print(f"  ⚠️  活動來源讀取失敗（{label}）：{e}")
    return events


def get_vietnam_events(limit=4):
    """
    彙整越南雙城 (胡志明市與河內) 近期活動，回傳最多 limit 筆。
    """
    print("🎭 正在取得胡志明市與河內活動資訊...")
    all_events = []

    # ── 胡志明市活動 ─────────────────────────────────────────────────────
    all_events.extend(_parse_feed(
        'https://news.google.com/rss/search?q="Ho+Chi+Minh+City"+AND+(event+OR+concert+OR+exhibition+OR+festival)+when:3d&hl=en-VN&gl=VN&ceid=VN:en',
        limit=3,
        label="HCMC Events (EN)"
    ))
    time.sleep(0.5)

    # ── 河內活動 ─────────────────────────────────────────────────────
    all_events.extend(_parse_feed(
        'https://news.google.com/rss/search?q="Hanoi"+AND+(event+OR+concert+OR+exhibition+OR+festival)+when:3d&hl=en-VN&gl=VN&ceid=VN:en',
        limit=3,
        label="Hanoi Events (EN)"
    ))
    time.sleep(0.5)

    # ── 中文越南活動 ─────────────────────────────────────────────────────
    all_events.extend(_parse_feed(
        'https://news.google.com/rss/search?q=(胡志明市+OR+河內+OR+越南)+AND+(活動+OR+展覽+OR+演唱會+OR+市集)+when:3d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant',
        limit=3,
        label="越南活動（中文）"
    ))
    time.sleep(0.5)

    # ── 台商活動 ─────────────────────────────────────────────────────────
    if len(all_events) < 3:
        all_events.extend(_parse_feed(
            'https://news.google.com/rss/search?q=台灣商會+越南+OR+台灣節+越南+when:7d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant',
            limit=2,
            label="台商活動"
        ))

    # ── 去重 ──────────────────────────────────────────────────────────────
    seen   = set()
    unique = []
    for ev in all_events:
        key = ev["title"].lower()[:60]
        if key not in seen:
            seen.add(key)
            unique.append(ev)

    selected = unique[:limit]
    if selected:
        print(f"  ✔️  找到 {len(selected)} 個越南雙城近期活動：")
        for ev in selected:
            print(f"     • [{ev['source']}] {ev['title']}")
    else:
        print("  ⚠️  今日未找到活動資訊。")

    return selected


if __name__ == "__main__":
    events = get_vietnam_events(limit=4)
    print("\n--- 越南雙城活動 ---")
    for ev in events:
        print(f"[{ev['source']}] {ev['title']}")
        print(f"  {ev['summary'][:120]}")
        print(f"  {ev['link']}\n")
