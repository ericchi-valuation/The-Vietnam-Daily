"""
Vietnam Cities Weather Fetcher
=================================
從 Open-Meteo 免費 API 取得河內與胡志明市今日天氣預報（無需 API Key）。
"""
import requests

# 胡志明市座標
HCMC_LAT = 10.8231
HCMC_LON = 106.6297

# 河內座標
HANOI_LAT = 21.0285
HANOI_LON = 105.8542

# WMO 天氣代碼對應中文描述
WMO_CODES = {
    0:  "晴空萬里",
    1:  "大致晴朗",
    2:  "多雲時晴",
    3:  "陰天",
    45: "霧",
    48: "凍霧",
    51: "小毛毛雨",
    53: "中等毛毛雨",
    55: "大毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "短暫小雨",
    81: "短暫中雨",
    82: "暴雨",
    95: "雷陣雨",
    96: "冰雹雷陣雨",
    99: "大冰雹雷陣雨",
}


def _fetch_city_weather(lat, lon, city_name):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "weathercode,windspeed_10m_max"
        "&current_weather=true"
        "&timezone=Asia%2FHo_Chi_Minh"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        daily   = data.get("daily", {})
        current = data.get("current_weather", {})

        temp_max  = daily.get("temperature_2m_max", [None])[0]
        temp_min  = daily.get("temperature_2m_min", [None])[0]
        precip    = daily.get("precipitation_sum",  [None])[0]
        wind      = daily.get("windspeed_10m_max",  [None])[0]
        wmo_code  = int(daily.get("weathercode", [0])[0] or 0)
        condition = WMO_CODES.get(wmo_code, "天氣多變")
        current_c = current.get("temperature")

        def to_f(c):
            return round(c * 9 / 5 + 32, 1) if c is not None else None

        summary = (
            f"{city_name}: {condition}。最高氣溫 {temp_max}°C，最低 {temp_min}°C。"
            f"風速最高 {wind} km/h。降雨量：{precip} mm。"
        )
        return {
            "city": city_name,
            "condition": condition,
            "temp_max_c": temp_max,
            "temp_min_c": temp_min,
            "wind_kmh": wind,
            "precip_mm": precip,
            "summary": summary
        }
    except Exception as e:
        print(f"  ⚠️  無法取得 {city_name} 天氣資料：{e}")
        return {
            "city": city_name,
            "condition": "資料無法取得",
            "summary": f"{city_name} 今日天氣資料暫時無法取得。"
        }


def get_vietnam_weather():
    """
    取得今日河內與胡志明市天氣預報。
    """
    print("🌤️  正在從 Open-Meteo 取得越南雙城天氣...")
    hanoi = _fetch_city_weather(HANOI_LAT, HANOI_LON, "河內")
    hcmc = _fetch_city_weather(HCMC_LAT, HCMC_LON, "胡志明市")
    
    print(f"  ✔️  {hanoi['summary']}")
    print(f"  ✔️  {hcmc['summary']}")
    
    return {"hanoi": hanoi, "hcmc": hcmc}


if __name__ == "__main__":
    w = get_vietnam_weather()
    print(w)
