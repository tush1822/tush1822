import MetaTrader5 as mt5
import pandas as pd
import requests
import schedule
import time
from datetime import datetime

# Telegram bot configuration
TELEGRAM_API_URL = "https://api.telegram.org/bot6730122299:AAE79IIvH-h8kVrisykb1hB1rGBV1PoZbJ4/sendMessage"
CHAT_ID = "1008290016"

def send_telegram_message(message):
    payload = {'chat_id': CHAT_ID, 'text': message}
    try:
        response = requests.post(TELEGRAM_API_URL, data=payload)
        response.raise_for_status()
        print("Telegram message sent:", message)
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")

# --- Initialize MetaTrader 5 ---
if not mt5.initialize("C:\\Program Files\\MetaTrader 5 IC Markets (SC)\\terminal64.exe"):
    print("MetaTrader5 initialization failed, error code =", mt5.last_error())
    quit()

login = 52097237
password1 = 'I7@dX5t$K9qZMC'
server = 'ICMarketsSC-Demo'

if not mt5.login(login, password1, server):
    print("Login failed, error code =", mt5.last_error())
    mt5.shutdown()
    quit()

symbols = [
    "GBPUSD", "EURUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDJPY",
    "XTIUSD", "XAUUSD", "XAGUSD",  
    "US500", "UK100", "DE40", "SWI20", "JP225", "CHINA50"
]
timeframe = mt5.TIMEFRAME_M1
timeframe_label = "M5"

def check_bb_rsi_strategy(symbol):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 50)
    if rates is None or len(rates) < 20:
        print(f"Not enough data for {symbol}")
        return
    
    df = pd.DataFrame(rates)
    df['close'] = df['close'].astype(float)

    # Convert timestamp to readable time
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # Bollinger Bands
    df['ma'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper'] = df['ma'] + 2 * df['std']
    df['lower'] = df['ma'] - 2 * df['std']

    # RSI Calculation
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # Get latest values
    latest = df.iloc[-1]
    timestamp = latest['time'].strftime('%Y-%m-%d %H:%M:%S')

    # --- BUY Condition ---
    if latest['close'] < latest['lower'] and latest['rsi'] < 30:
        message = (
            f"📈 BUY Signal - {symbol} met BB & RSI conditions at {timeframe_label}\n"
            f"Time: {timestamp}\n"
            f"Price: {latest['close']:.5f}, RSI: {latest['rsi']:.2f}"
        )
        send_telegram_message(message)

    # --- SELL Condition ---
    elif latest['close'] > latest['upper'] and latest['rsi'] > 70:
        message = (
            f"📉 SELL Signal - {symbol} met BB & RSI conditions at {timeframe_label}\n"
            f"Time: {timestamp}\n"
            f"Price: {latest['close']:.5f}, RSI: {latest['rsi']:.2f}"
        )
        send_telegram_message(message)
    
    else:
        print(f"{symbol}: No signal | Time: {timestamp} | Price: {latest['close']:.5f} | RSI: {latest['rsi']:.2f}")

def run_strategy_check():
    for symbol in symbols:
        check_bb_rsi_strategy(symbol)

# Schedule every 5 seconds
schedule.every(5).seconds.do(run_strategy_check)

try:
    while True:
        schedule.run_pending()
        time.sleep(10)
except KeyboardInterrupt:
    print("Script interrupted.")
finally:
    mt5.shutdown()
    print("MetaTrader 5 shutdown.")
