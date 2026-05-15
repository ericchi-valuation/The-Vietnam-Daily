import os
import sys
import datetime
import pytz

from core.content_reformatter import reformat_for_newsletter, reformat_for_threads

def verify_environment():
    required_keys = [
        "GEMINI_API_KEY",
        "ELEVENLABS_API_KEY",
        "GMAIL_ADDRESS",
        "GMAIL_APP_PASSWORD",
        "THREADS_USER_ID",
        "THREADS_ACCESS_TOKEN"
    ]
    missing = [key for key in required_keys if not os.getenv(key)]

    print("\n🔍 [Health Check] Verifying environment variables...")
    if missing:
        print(f"  ⚠️  缺少環境變數: {', '.join(missing)}")
        print("  (工作流程會繼續，但部分發布功能可能會跳過或使用免費方案)\n")
    else:
        print("  ✅ 所有環境變數檢查通過。\n")

def main():
    from fetchers.news_fetcher import get_daily_news
    from fetchers.social_fetcher import get_social_trending
    from fetchers.weather_fetcher import get_vietnam_weather
    from fetchers.exchange_rate_fetcher import get_exchange_rates
    from fetchers.events_fetcher import get_vietnam_events
    from core.script_generator import generate_podcast_script, review_and_improve_script

    verify_environment()

    tz_str = os.environ.get("TZ", "Asia/Ho_Chi_Minh")
    tz = pytz.timezone(tz_str)
    today_str = datetime.datetime.now(tz).strftime("%Y年%m月%d日")
    today_iso = datetime.datetime.now(tz).strftime("%Y-%m-%d")

    print("=" * 50)
    print(f"🎙️  越南晨間快訊 Good Morning Vietnam — Pipeline starting for {today_str}")
    print("=" * 50)

    # ── Step 1: Fetch all data ──────────────────────────────────────────────
    print("\n📡 Step 1/5: 正在獲取最新越南商業與科技新聞...")
    news_data = get_daily_news(items_per_source=3)
    total_news = sum(len(a) for a in news_data.values())
    print(f"  ✔️ 從 {len(news_data)} 個新聞來源中收集了 {total_news} 篇文章。")

    print("\n🌤️  Step 1b: 正在獲取越南雙城 (河內 & 胡志明市) 天氣...")
    weather_data = get_vietnam_weather()

    print("\n💱  Step 1c: 正在獲取匯率 (USD/VND, CNY/VND, TWD/VND)...")
    exchange_data = get_exchange_rates()

    print("\n💬 Step 1d: 正在獲取社群熱議話題 (PTT / 越南群組)...")
    social_data = get_social_trending(limit_per_source=3)
    print(f"  ✔️ 收集了 {len(social_data)} 則熱門話題。")

    print("\n🎭 Step 1e: 正在獲取越南在地活動 (河內 & 胡志明市)...")
    events_data = get_vietnam_events(limit=4)

    # ── Step 1f: Read Sponsor Text ──────────────────────────────────────────
    sponsor_text = None
    if os.path.exists("sponsor.txt"):
        try:
            with open("sponsor.txt", "r", encoding="utf-8") as f:
                sponsor_text = f.read().strip()
            if sponsor_text:
                print(f"  ✔️  偵測到贊助商訊息: '{sponsor_text[:40]}...'")
        except Exception as e:
            print(f"  ⚠️  無法讀取 sponsor.txt: {e}")

    # ── Step 2: Generate AI podcast script ─────────────────────────────────
    print("\n🤖 Step 2/5: 使用 AI 生成 Podcast 講稿與摘要...")
    script = generate_podcast_script(
        news_data,
        social_data,
        weather_data,
        exchange_data,
        events_data=events_data,
        sponsor_text=sponsor_text
    )

    if not script:
        print("❌ 講稿生成失敗，停止工作流程。")
        sys.exit(1)

    print(f"  ✔️ 初稿生成完畢 ({len(script)} 字元)。")

    print("\n📝 Step 2b/5: 進入 AI 編輯審稿流程 (長度與語氣檢查)...")
    script = review_and_improve_script(script)

    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    print(f"  ✔️ 最終版講稿已儲存 ({len(script)} 字元)。準備進行語音合成。")

    # ── Step 3: Build TTS audio ─────────────────────────────────────────────
    print("\n🎤 Step 3/5: 將文字轉換為廣播音檔 (TTS)...")
    raw_voice_file = "VietnamDaily_Podcast.mp3"
    final_file     = "VietnamDaily_Podcast_Final.mp3"
    bgm_file       = "bgm.mp3"

    from core.audio_builder import build_podcast_audio
    build_podcast_audio(script_file="script.txt", output_file=raw_voice_file)

    if not os.path.exists(raw_voice_file) or os.path.getsize(raw_voice_file) == 0:
        print("❌ 語音合成失敗，停止工作流程。")
        sys.exit(1)
    print(f"  ✔️ 人聲原始檔就緒: {raw_voice_file}")

    # ── Step 4: Mix BGM with voice ──────────────────────────────────────────
    print("\n🎵 Step 4/5: 正在進行背景音樂混音...")
    from core.audio_mixer import mix_podcast_audio
    if os.path.exists(bgm_file):
        try:
            mix_podcast_audio(voice_file=raw_voice_file, bgm_file=bgm_file, output_file=final_file)
            print(f"  ✔️ 最終混音版本就緒: {final_file}")
        except Exception as e:
            print(f"  ⚠️ 混音失敗 ({e})。將使用純人聲版本作為最終輸出。")
            import shutil
            shutil.copy(raw_voice_file, final_file)
    else:
        print(f"  ⚠️ 找不到配樂檔 '{bgm_file}'。將使用純人聲版本作為最終輸出。")
        import shutil
        shutil.copy(raw_voice_file, final_file)

    # ── Step 5: Publish ─────────────────────────────────────────────────────
    print("\n📢 Step 5/5: 發布與推送內容...")

    # 5a. Newsletter
    try:
        with open("script.txt", "r", encoding="utf-8") as f:
            script_text = f.read()
        html_content = reformat_for_newsletter(script_text, events_data=events_data)
        from publishers.email_sender import send_newsletter
        send_newsletter(f"越南晨間快訊 Good Morning Vietnam — {today_iso}", html_content)
    except Exception as e:
        print(f"  ⚠️ 電子報寄發失敗: {e}")

    # 5b. Threads
    try:
        with open("script.txt", "r", encoding="utf-8") as f:
            script_text = f.read()
        threads_post = reformat_for_threads(script_text)
        from publishers.threads_poster import post_to_threads
        post_to_threads(threads_post)
    except Exception as e:
        print(f"  ⚠️ Threads 發布失敗: {e}")

    print("\n" + "=" * 50)
    print(f"✅ 流程完成！ '{final_file}' 已準備好上傳各大平台。")
    print("=" * 50)

if __name__ == "__main__":
    main()
