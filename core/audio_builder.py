import os
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()

def generate_audio_elevenlabs(script_text, output_file):
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key or api_key == "your_elevenlabs_api_key_here":
        return False
        
    print("\n[Audio] 偵測到 ElevenLabs API Key，正在呼叫語音庫...")
    url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB" 
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": script_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,         # 稍微降低穩定度，增加語氣起伏
            "similarity_boost": 0.7,   # 提高相似度，確保聲音特徵鮮明
            "style": 0.06,             # 增加一點風格表現
            "use_speaker_boost": True
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        return True
    else:
        print(f"ElevenLabs 錯誤: {response.text}")
        return False

async def generate_audio_edge(script_text, output_file):
    print("\n[Audio] 自動切換至完全免費的微軟 Azure 語音 (Edge TTS)...")
    import edge_tts
    # 選擇中文女聲 (HsiaoChenNeural 為台灣專業女聲)
    voice = "zh-TW-HsiaoChenNeural" 
    communicate = edge_tts.Communicate(script_text, voice, rate="+5%")
    await communicate.save(output_file)
    return True

def build_podcast_audio(script_file="script.txt", output_file="podcast.mp3"):
    if not os.path.exists(script_file):
        print(f"找不到講稿: {script_file}")
        return
        
    try:
        with open(script_file, "r", encoding="utf-8-sig") as f:
            script_text = f.read()
    except UnicodeDecodeError:
        with open(script_file, "r", encoding="mbcs") as f:
            script_text = f.read()

    import re
    script_text = re.sub(r'\[.*?\]', '', script_text)
    script_text = re.sub(r'\(.*?\)', '', script_text)
    script_text = script_text.replace('*', '')
    script_text = script_text.replace('#', '')
    script_text = script_text.replace('_', '')
    script_text = script_text.replace('---', ' ')
    script_text = re.sub(r'\n{3,}', '\n\n', script_text)

    success = generate_audio_elevenlabs(script_text, output_file)
    
    if not success:
        try:
            asyncio.run(generate_audio_edge(script_text, output_file))
            success = True
        except ImportError:
            print("\n❌ 尚未安裝 edge-tts 套件，請執行：pip install edge-tts")
            return
            
    if success:
        print(f"\n🎧 廣播生成大功告成！檔案已儲存為：{output_file}")

if __name__ == "__main__":
    build_podcast_audio()
