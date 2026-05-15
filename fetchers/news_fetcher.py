"""
Vietnam News Fetcher（越南中文每日新聞爬蟲）
=============================================
針對在越南生活的華人、台商與中文商務人士，
從以下來源收集越南相關的中文與英文新聞：

新聞來源：
  1. VnExpress 國際版（英文）
  2. Vietnam Investment Review（英文）
  3. Vietnam Briefing（英文）
  4. Google News – 越南中文搜尋（越南 + 台商 + 華人）
  5. Google News – 越南經濟英文
  6. Google News – 胡志明市商業
  7. Google News – 越南製造業 / 外資
  8. 鉅亨網 – 越南相關
  9. ETtoday – 越南相關
"""

import feedparser
import time
from datetime import datetime, timezone, timedelta

GOSSIP_KEYWORDS = [
    'celebrity', 'scandal', 'leaked', 'nsfw', 'affair',
    '八卦', '偷吃', '摩鐵', '走光', '出軌', '豔照'
]


def is_trash_news(title, summary=""):
    text = (title + summary).lower()
    return any(kw in text for kw in GOSSIP_KEYWORDS)


def _is_recent(entry, max_hours=36):
    for attr in ('published_parsed', 'updated_parsed'):
        t = getattr(entry, attr, None)
        if t is None:
            continue
        try:
            pub_utc = datetime(*t[:6], tzinfo=timezone.utc)
            cutoff  = datetime.now(timezone.utc) - timedelta(hours=max_hours)
            return pub_utc >= cutoff
        except Exception:
            continue
    return True


def fetch_rss_news(feed_url, limit=3, max_retries=3, max_hours=36):
    """從單一 RSS 來源抓取最新文章（限制 max_hours 小時內）。"""
    entries = []
    for attempt in range(max_retries):
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return entries

            for entry in feed.entries:
                if len(entries) >= limit:
                    break
                if not _is_recent(entry, max_hours=max_hours):
                    continue
                title   = entry.get('title', '').strip()
                summary = entry.get('summary', entry.get('description', ''))
                if not title:
                    continue
                if is_trash_news(title, summary):
                    continue
                entries.append({
                    'title':   title,
                    'summary': summary,
                    'link':    entry.get('link', '')
                })
            return entries

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print(f"Error parsing feed {feed_url}: {e}")
                return entries
    return entries


def get_daily_news(items_per_source=2):
    """
    彙整越南相關中英文新聞，供 AI 腳本生成使用。
    目標聽眾：在越南生活的華人、台商、新南向相關商務人士。
    """
    sources = {
        # ── 越南英文主流媒體 ──────────────────────────────────────────
        'VnExpress International': 'https://e.vnexpress.net/rss/news/business.rss',
        'Vietnam Investment Review (VIR)': (
            'https://news.google.com/rss/search?q=site:vir.com.vn+when:2d'
            '&hl=en-VN&gl=VN&ceid=VN:en'
        ),
        'Vietnam Briefing (Economy)': (
            'https://news.google.com/rss/search?q=site:vietnam-briefing.com+when:2d'
            '&hl=en&gl=US&ceid=US:en'
        ),

        # ── Google News 越南中文搜尋 ──────────────────────────────────
        'Google新聞 – 越南台商': (
            'https://news.google.com/rss/search?q=越南+台商+OR+投資+OR+工廠+when:2d'
            '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
        ),
        'Google新聞 – 越南華人': (
            'https://news.google.com/rss/search?q=越南+華人+OR+胡志明市+OR+台灣人+when:2d'
            '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
        ),
        'Google新聞 – 越南新南向': (
            'https://news.google.com/rss/search?q=越南+新南向+OR+勞工+OR+移工+when:2d'
            '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
        ),

        # ── Google News 英文越南財經 ──────────────────────────────────
        'Google News – Vietnam Economy': (
            'https://news.google.com/rss/search?q=Vietnam+economy+GDP+inflation+when:2d'
            '&hl=en-VN&gl=VN&ceid=VN:en'
        ),
        'Google News – Hanoi City': (
            'https://news.google.com/rss/search?q="Hanoi"+business+real+estate+when:2d'
            '&hl=en-VN&gl=VN&ceid=VN:en'
        ),
        'Google News – Ho Chi Minh City': (
            'https://news.google.com/rss/search?q="Ho Chi Minh City"+business+real+estate+when:2d'
            '&hl=en-VN&gl=VN&ceid=VN:en'
        ),
        'Google News – Vietnam Manufacturing FDI': (
            'https://news.google.com/rss/search?q=Vietnam+manufacturing+FDI+factory+supply+chain+when:2d'
            '&hl=en&gl=US&ceid=US:en'
        ),
        'Google News – Vietnam Tech': (
            'https://news.google.com/rss/search?q=Vietnam+semiconductor+technology+startup+when:2d'
            '&hl=en&gl=US&ceid=US:en'
        ),

        # ── 台灣財經媒體越南相關報導 ──────────────────────────────────
        '鉅亨網 – 越南': (
            'https://news.google.com/rss/search?q=site:cnyes.com+越南+when:2d'
            '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
        ),
        'ETtoday – 越南': (
            'https://news.google.com/rss/search?q=site:ettoday.net+越南+when:2d'
            '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
        ),
    }

    all_news = {}
    for source_name, url in sources.items():
        try:
            articles = fetch_rss_news(url, limit=items_per_source)
            if articles:
                all_news[source_name] = articles
                print(f"  ✔️  [{source_name}] {len(articles)} 篇")
        except Exception as e:
            print(f"Failed to fetch {source_name}: {e}")

    return all_news


if __name__ == "__main__":
    news = get_daily_news(2)
    for source, articles in news.items():
        print(f"--- {source} ---")
        for a in articles:
            print(f"  [{a['title']}]")
