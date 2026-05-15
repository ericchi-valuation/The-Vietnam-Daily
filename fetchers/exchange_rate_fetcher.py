"""
Vietnam VND Exchange Rate Fetcher
====================================
取得越南盾（VND）對美元（USD）、人民幣（CNY）、新台幣（TWD）的即時匯率。
同時計算與前一交易日的漲跌幅，啟用智慧型波動度判斷。

使用 Frankfurter API（免費，無需 API Key），以 EUR 為基準交叉推算 VND。
由於 VND 波動幅度遠小於 EUR/HUF，波動門檻設定為 0.5%。
"""
import requests
from datetime import datetime, timedelta
import pytz

HCMC_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
VOLATILITY_THRESHOLD = 0.5  # VND 波動門檻（%）


def _get_prev_business_day_from(date_str: str) -> str:
    anchor = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=HCMC_TZ)
    day = anchor - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day.strftime("%Y-%m-%d")


def get_exchange_rates():
    """
    取得 USD→VND、CNY→VND、TWD→VND 的即時匯率與前日比較。

    回傳 dict，欄位說明：
      - usd_vnd, cny_vnd, twd_vnd     : 今日匯率
      - usd_vnd_prev, cny_vnd_prev     : 前一交易日匯率
      - usd_change_pct, cny_change_pct : 漲跌幅（%）
      - high_volatility                : 是否高波動
      - summary                        : 一行摘要（供腳本使用）
    """
    result = {
        "usd_vnd":        None,
        "cny_vnd":        None,
        "twd_vnd":        None,
        "usd_vnd_prev":   None,
        "cny_vnd_prev":   None,
        "usd_change_pct": None,
        "cny_change_pct": None,
        "high_volatility": False,
        "summary": "匯率資料暫時無法取得。"
    }

    latest_date = None

    # ── 今日匯率（以 USD 為基準，換算 VND、CNY、TWD）────────────────────────
    try:
        print("💱 正在從 ExchangeRate-API 取得今日越南盾匯率...")
        resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("rates", {})

        vnd = rates.get("VND")
        cny = rates.get("CNY")
        twd = rates.get("TWD")

        if vnd:
            result["usd_vnd"] = round(vnd, 0)
        if cny and vnd:
            # CNY→VND = VND/USD ÷ CNY/USD
            result["cny_vnd"] = round(vnd / cny, 1)
        if twd and vnd:
            result["twd_vnd"] = round(vnd / twd, 1)

        raw_ts = data.get("time_last_update_utc", "")
        if raw_ts:
            try:
                latest_date = datetime.strptime(raw_ts, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
            except ValueError:
                pass

        if result["usd_vnd"]:
            print(f"  ✔️  今日（{latest_date}）：1 USD = {result['usd_vnd']:,.0f} VND | "
                  f"1 CNY = {result['cny_vnd']:,.1f} VND | 1 TWD = {result['twd_vnd']:,.1f} VND")

    except Exception as e:
        print(f"  ⚠️  無法取得今日匯率：{e}")

    # ── 前一交易日匯率 ─────────────────────────────────────────────────────
    if latest_date:
        prev_day_str = _get_prev_business_day_from(latest_date)
    else:
        fallback = datetime.now(HCMC_TZ) - timedelta(days=2)
        while fallback.weekday() >= 5:
            fallback -= timedelta(days=1)
        prev_day_str = fallback.strftime("%Y-%m-%d")

    try:
        print(f"💱 正在取得前一交易日匯率（{prev_day_str}）以計算波動度...")
        hist = requests.get(
            f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{prev_day_str}/v1/currencies/usd.json",
            timeout=10
        )
        if hist.status_code == 200:
            prev_rates = hist.json().get("usd", {})
            vnd_prev = prev_rates.get("vnd")
            cny_prev = prev_rates.get("cny")
            if vnd_prev:
                result["usd_vnd_prev"] = round(float(vnd_prev), 0)
            if vnd_prev and cny_prev:
                result["cny_vnd_prev"] = round(float(vnd_prev) / float(cny_prev), 1)
            if result["usd_vnd_prev"]:
                print(f"  ✔️  前一交易日：1 USD = {result['usd_vnd_prev']:,.0f} VND | "
                      f"1 CNY = {result['cny_vnd_prev']:,.1f} VND")
    except Exception as e:
        print(f"  ⚠️  無法取得前日匯率：{e}")

    # ── 計算漲跌幅與波動度 ─────────────────────────────────────────────────
    if result["usd_vnd"] and result["usd_vnd_prev"]:
        result["usd_change_pct"] = round(
            (result["usd_vnd"] - result["usd_vnd_prev"]) / result["usd_vnd_prev"] * 100, 3
        )
    if result["cny_vnd"] and result["cny_vnd_prev"]:
        result["cny_change_pct"] = round(
            (result["cny_vnd"] - result["cny_vnd_prev"]) / result["cny_vnd_prev"] * 100, 3
        )

    usd_vol = abs(result["usd_change_pct"]) if result["usd_change_pct"] is not None else 0
    cny_vol = abs(result["cny_change_pct"]) if result["cny_change_pct"] is not None else 0
    result["high_volatility"] = (usd_vol >= VOLATILITY_THRESHOLD or cny_vol >= VOLATILITY_THRESHOLD)

    # ── 組合摘要文字 ──────────────────────────────────────────────────────
    if result["usd_vnd"]:
        trend_usd = ""
        if result["usd_change_pct"] is not None:
            sign = "+" if result["usd_change_pct"] >= 0 else ""
            trend_usd = f"（{sign}{result['usd_change_pct']}%）"

        trend_cny = ""
        if result["cny_change_pct"] is not None:
            sign = "+" if result["cny_change_pct"] >= 0 else ""
            trend_cny = f"（{sign}{result['cny_change_pct']}%）"

        result["summary"] = (
            f"1 美元 = {result['usd_vnd']:,.0f} 越南盾{trend_usd} | "
            f"1 人民幣 = {result['cny_vnd']:,.1f} 越南盾{trend_cny}"
        )
        if result.get("twd_vnd"):
            result["summary"] += f" | 1 新台幣 = {result['twd_vnd']:,.1f} 越南盾"

        vol_label = "⚠️  高波動" if result["high_volatility"] else "✅ 低波動"
        print(f"  {vol_label} — {result['summary']}")

    return result


if __name__ == "__main__":
    rates = get_exchange_rates()
    print("\n完整結果：")
    for k, v in rates.items():
        print(f"  {k}: {v}")
