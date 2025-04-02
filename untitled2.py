
import ccxt
import pandas as pd
import pandas_ta as ta
import asyncio
import nest_asyncio   # ✅ Fix for Colab/Jupyter
from telegram import Bot
import pytz


# ✅ Apply the patch for nested event loops (Fixes RuntimeError)
nest_asyncio.apply()

# ✅ Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = "8109127375:AAFAjPAtcSTSrmjPYnb7JOBB59OnMUpR6Wo"
TELEGRAM_CHAT_ID = "1058611753"

# ✅ Initialize Telegram Bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ✅ Initialize Delta Exchange API
exchange = ccxt.delta({
    'apiKey': 'eiSk0NrGYUcKLwCmAwdivzpguN8nf9',
    'secret': 'un1uOVSLdj2D3wY5WSzeHq6EL2S2wWlc8wuVXOeL1fC43Ji0ZpCzzGE5i1HK'
})

# ✅ Set Your Timezone (Change if needed)
LOCAL_TZ = pytz.timezone("Asia/Kolkata")  # Set your local timezone

# ✅ Function to Fetch Historical Data
def fetch_historical_data(symbol="ETHUSD", timeframe="5m", limit=150):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])

        # Convert timestamp to local timezone
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert(LOCAL_TZ)
        df.set_index("timestamp", inplace=True)

        return df
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None

# ✅ Calculate Supertrend & EMA
def calculate_indicators(df):
    if df is None or df.empty:
        return None

    df = df[~df.index.duplicated(keep="last")]  # Remove duplicate timestamps

    # ✅ Supertrend (ATR 10, Multiplier 3)
    supertrend = ta.supertrend(df["high"], df["low"], df["close"], length=10, multiplier=3)
    df["Supertrend"] = supertrend["SUPERTd_10_3.0"].ffill()  # Fill missing values


    # ✅ EMA 72
    df["EMA72"] = ta.ema(df["close"], length=72)

    return df

# ✅ Send Telegram Alert
async def send_telegram_alert(signal, price):
    message = f"🚀 {signal} Signal for ETH @ {price}"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# ✅ Check Buy/Sell Signals
async def check_signals():
    df = fetch_historical_data()
    if df is None:
        print("❌ No data available!")
        return

    df = calculate_indicators(df)
    if df is None:
        print("❌ Indicator calculation failed!")
        return

    print(df.tail(5))  # ✅ Debugging: Print last 5 candles

    latest = df.iloc[-2]  # ✅ Use the second-last candle (confirmed close)
    prev = df.iloc[-3]  # ✅ Check previous candle for trend confirmation

    print(f"🕒 Latest Close: {latest['close']} | Supertrend: {latest['Supertrend']} | EMA72: {latest['EMA72']}")

    # ✅ Confirm Supertrend Flip + EMA Cross
    if prev["Supertrend"] != latest["Supertrend"]:
        if latest["Supertrend"] == 1 and latest["close"] > latest["EMA72"]:  # Buy Condition
            print(f"✅ BUY Signal: ETH @ {latest['close']}")
            await send_telegram_alert("BUY", latest["close"])
        elif latest["Supertrend"] == -1 and latest["close"] < latest["EMA72"]:  # Sell Condition
            print(f"❌ SELL Signal: ETH @ {latest['close']}")
            await send_telegram_alert("SELL", latest["close"])
        else:
            print("⏳ No trade signal.")
    else:
        print("📉 No Supertrend flip. Waiting for a clear trend change.")

# ✅ Run Bot Every 5 Minutes (for Continuous Monitoring)
async def run_bot():
    while True:
        await check_signals()
        await asyncio.sleep(300)  # 5-minute interval

# ✅ Run the bot correctly to avoid runtime errors
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run_bot())  # ✅ Fixes 'RuntimeError: Event loop is already running'

