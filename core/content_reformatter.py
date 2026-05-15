import os
from google import genai
from google.genai import types

def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def reformat_for_newsletter(podcast_script, events_data=None):
    """
    將原版廣播口語稿，改寫成排版精美、適合人眼閱讀的 HTML 電子報格式。
    如果提供了 events_data，會在電子報最後附加一個互動式的“Today in Vietnam”活動區塊。
    """
    client = _get_gemini_client()
    if not client:
        return "<p>（無法生成電子報此內容，因為缺少 Gemini API Key）</p>"
        
    print("🤖 正在使用 AI 將廣播稿改寫為電子報 HTML 格式...")

    events_html_block = ""
    if events_data:
        events_items = ""
        for ev in events_data:
            title   = ev.get('title', '').strip()
            summary = ev.get('summary', '').strip()
            link    = ev.get('link', '').strip()
            source  = ev.get('source', '').strip()
            if not title:
                continue
            link_tag = f' <a href="{link}" style="color:#d32f2f;font-size:0.85em;">→ 了解更多</a>' if link else ''
            events_items += (
                f'<li style="margin-bottom:10px;">'
                f'<strong>{title}</strong>{link_tag}'
                f'<br><span style="color:#555;font-size:0.9em;">{summary}</span>'
                f'<br><span style="color:#aaa;font-size:0.8em;">來源: {source}</span>'
                f'</li>'
            )
        if events_items:
            events_html_block = (
                '<hr style="margin:24px 0;">'
                '<h2 style="color:#d32f2f;">&#127979; 越南在地活動報報</h2>'
                f'<ul style="padding-left:18px;">{events_items}</ul>'
                '<p style="margin-top:14px;font-size:0.9em;color:#444;">'
                '💬 <strong>知道這個週末哪裡有好玩的嗎？</strong> '
                '直接回覆這封信與我們分享，我們可能會在之後的節目中為大家介紹喔！'
                '</p>'
            )
    
    prompt = f"""
    You are an expert tech and business newsletter editor for a Chinese-language audience in Vietnam.
    I'm providing you with a script that was designed to be read out loud as a podcast.
    Your task is to convert this spoken text into a clean, highly engaging HTML newsletter format in Traditional Chinese (繁體中文).
    
    Requirements:
    1. Output ONLY valid HTML code. Do NOT output markdown formatting like ```html.
    2. Use semantic HTML tags: <h2> for main news topics, <ul>/<li> for bullet points, <strong> for emphasis.
    3. Remove any podcast-specific filler words (like "歡迎收聽", "我是你的主持人", "今天的節目就到這裡").
    4. Start immediately with: <h1>越南晨間快訊 Good Morning Vietnam</h1><p>以下是為您整理的今日重點新聞：</p>.
    5. Summarize the stories slightly if the spoken text is too verbose.
    6. Tone: Professional, forward-thinking, and easy to skim.
    7. At the very end of the HTML, after all news content, insert exactly this placeholder without modification: {{EVENTS_BLOCK}}
    8. After the events block placeholder, add a short sign-off paragraph in a <p> tag that says: "覺得這份電子報有幫助嗎？歡迎轉發給在越南打拼的朋友，或<a href='https://github.com/ericchi-valuation'>訂閱我們的 Podcast</a> 隨時隨地掌握最新動態。"
    
    Here is the podcast script:
    {podcast_script}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        html_text = response.text.replace("```html", "").replace("```", "").strip()
        html_text = html_text.replace("{EVENTS_BLOCK}", events_html_block)
        return html_text
    except Exception as e:
        print(f"❌ 生成電子報內容失敗: {e}")
        return f"<p>生成電子報時發生錯誤: {podcast_script[:100]}...</p>"

def reformat_for_threads(podcast_script):
    """
    將原版廣播口語稿，改寫成精簡的社群貼文短語 (Threads 版)。
    """
    client = _get_gemini_client()
    if not client:
        return "新一集的越南晨間快訊 Good Morning Vietnam 上架啦！點擊主頁連結收聽最新節目🎧"

    print("🤖 正在使用 AI 萃取 Threads 貼文精華短語...")
    
    prompt = f"""
    You are a witty, professional social media manager for a Tech and Business podcast in Vietnam.
    Read the following podcast script and create a single post for Threads in Traditional Chinese (繁體中文).
    
    CRITICAL REQUIREMENTS:
    1. You MUST include 2 or 3 bullet points summarizing the actual news headlines from the script. Give me the facts.
    2. STRICT FACTUALITY: Do NOT invent, hallucinate, or assume any numbers, dates, stock prices, or exchange rates.
       ONLY use facts and figures EXPLICITLY stated word-for-word in the script.
    3. The entire output MUST be strictly UNDER 450 characters.
    4. Use 1 or 2 relevant emojis.
    5. Do NOT use HTML formatting. Use plain text and line breaks.
    6. End the post with: "點擊連結收聽完整內容！🎧".
    7. Do not include any title like "Threads Post:". Just return the text.
    
    Here is the podcast script:
    {podcast_script}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2, 
            )
        )
        result_text = response.text.strip()
        print("\n👀 [Debug] Gemini 生成的 Threads 貼文結果如下：")
        print("-" * 30)
        print(result_text)
        print("-" * 30 + "\n")
        return result_text
    except Exception as e:
        print(f"❌ 生成 Threads 貼文失敗: {e}")
        return "[自動生成失敗] 新一集的越南晨間快訊 Good Morning Vietnam 上線囉！點擊連結收聽最新節目🎧"
