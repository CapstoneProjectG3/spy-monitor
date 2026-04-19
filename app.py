import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Institutional SPY Monitor", layout="centered")

# --- CUSTOM CSS FOR MOBILE ---
st.markdown("""<style> .stApp { background-color: #0e1117; color: white; } </style>""", unsafe_allow_html=True)

def get_data(symbol, interval, period):
    df = yf.download(symbol, period=period, interval=interval)
    # Calculate Institutional Indicators
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA50'] = ta.ema(df['Close'], length=50)
    df['EMA200'] = ta.ema(df['Close'], length=200)
    df['VWAP'] = ta.vwap(df.High, df.Low, df.Close, df.Volume)
    return df

# --- 1. ANALYSIS LAYER (The Strategy) ---
symbol = "SPY"
df_1h = get_data(symbol, "1h", "1mo")
df_5m = get_data(symbol, "5m", "5d")
df_2m = get_data(symbol, "2m", "2d")

# Current Status
last_h = df_1h.iloc[-1]
last_5 = df_5m.iloc[-1]
last_2 = df_2m.iloc[-1]

# --- 2. THE SIGNAL ENGINE ---
st.title("🦅 SPY Alpha Monitor")

# Trend Bias (1 Hour)
trend = "BULLISH" if last_h['Close'] > last_h['EMA200'] else "BEARISH"
trend_color = "green" if trend == "BULLISH" else "red"

st.markdown(f"### 1H Trend: <span style='color:{trend_color}'>{trend}</span>", unsafe_allow_html=True)

# Confluence Logic (The "Institutional Buy")
is_above_vwap = last_5['Close'] > last_5['VWAP']
is_above_200 = last_5['Close'] > last_5['EMA200']
ema_9_pullback = last_2['Low'] <= last_2['EMA9'] and last_2['Close'] > last_2['EMA9']

# --- 3. UI DASHBOARD ---
col1, col2 = st.columns(2)
col1.metric("Current Price", f"${last_2['Close']:.2f}")
col2.metric("VWAP", f"${last_2['VWAP']:.2f}", delta=f"{last_2['Close'] - last_2['VWAP']:.2f}")

if trend == "BULLISH" and is_above_vwap and is_above_200:
    if ema_9_pullback:
        st.success("🎯 SIGNAL: 2m EMA9 CATCH! Institutional Confluence is Solid.")
    else:
        st.warning("⚖️ WAIT: Trending Up, but wait for EMA9 Pullback to enter.")
elif trend == "BEARISH" and not is_above_vwap and not is_above_200:
    st.error("📉 SIGNAL: Institutional SHORT. Below VWAP/200/50.")
else:
    st.info("⌛ NO TRADE: Choppy Zone. Wait for direction.")

# --- 4. THE CHART (Plotly for Mobile) ---
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df_5m.index, open=df_5m['Open'], high=df_5m['High'], low=df_5m['Low'], close=df_5m['Close'], name="Price"))
fig.add_trace(go.Scatter(x=df_5m.index, y=df_5m['EMA200'], line=dict(color='orange', width=2), name="200 EMA"))
fig.add_trace(go.Scatter(x=df_5m.index, y=df_5m['VWAP'], line=dict(color='cyan', width=1, dash='dot'), name="VWAP"))
fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

st.write("📌 **Rule:** Only enter if 5m candle closes above 9 EMA. Exit on 1m cross.")
