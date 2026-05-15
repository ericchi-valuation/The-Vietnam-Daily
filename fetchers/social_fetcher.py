"""
Vietnam Social Media Trending Fetcher
=======================================
爬取越南華人、台商社群的熱門討論話題，供 AI 播報使用。

來源：
  1. 批踢踢（PTT）– 海外台灣版（Oversea）
  2. Google News 搜尋 – 越南台商討論
  3. Google News 搜尋 – 越南生活 / 華人移民社群
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TRASH_KEYWORDS = [
    '乳', '奶', '性愛', '做愛', '約炮', '外流', '色情', '🔞',
    '裸', '走光', '偷拍', 'nsfw'
]


def is_trash_social(title):
    text = title.lower()
    return any(kw in text for kw in TRASH_KEYWORDS)


def get_ptt_oversea_trending(limit=3):
    """爬取 PTT 海外版（海外台灣人討論熱點）。"""
    url = "https://www.ptt.cc/bbs/Oversea_Job/index.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    cookies = {'over18': '1'}

    try:
        response = requests.get(url, headers=headers, cookies=cookies, verify=False, timeout=8)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = []
        for div in soup.find_all('div', class_='r-ent')[:limit + 3]:
            title_tag = div.find('div', class_='title')
            if title_tag:
                a = title_tag.find('a')
                if a:
                    title = a.text.strip()
                    if '公告' not in title and not is_trash_social(title):
                        posts.append({
                            'title':  title,
                            'url':    'https://www.ptt.cc' + a['href'],
                            'topics': ['PTT 海外打工板']
                        })
                        if len(posts) >= limit:
                            break
        return posts
    except Exception as e:
        print(f"PTT 海外版抓取失敗：{e}")
        return []


def get_vietnam_discussion_trending(limit=3):
    """透過 Google News RSS 搜尋越南台商社群熱門討論。"""
    url = (
        'https://news.google.com/rss/search?q=越南+台商+OR+華人+OR+移工+生活+when:2d'
        '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
    )
    try:
        feed = feedparser.parse(url)
        posts = []
        for entry in feed.entries[:limit * 2]:
            title = entry.get('title', '').strip()
            if is_trash_social(title):
                continue
            posts.append({
                'title':  title,
                'url':    entry.get('link', ''),
                'topics': ['越南社群討論']
            })
            if len(posts) >= limit:
                break
        return posts
    except Exception as e:
        print(f"越南討論熱點抓取失敗：{e}")
        return []


def get_social_trending(limit_per_source=2):
    """彙整 PTT 海外版與越南社群討論的熱門話題。"""
    posts = []
    posts.extend(get_ptt_oversea_trending(limit=limit_per_source))
    posts.extend(get_vietnam_discussion_trending(limit=limit_per_source))
    return posts


if __name__ == "__main__":
    hot_topics = get_social_trending()
    print("--- 越南台商社群熱門話題 ---")
    for topic in hot_topics:
        print(f"標題：{topic['title']}")
        print(f"來源：{topic['topics']}\n")
