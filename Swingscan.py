import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import datetime

# ==================== SCAN FUNKTION ====================
def scan_stock(ticker, period='1y', interval='1d'):
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data.empty or len(data) < 200:
            return None

        # --- Technische Indikatoren mit pandas-ta ---
        data['SMA50']  = ta.sma(data['Close'], length=50)
        data['SMA200'] = ta.sma(data['Close'], length=200)
        data['RSI']    = ta.rsi(data['Close'], length=14)
        data['ATR']    = ta.atr(data['High'], data['Low'], data['Close'], length=14)

        macd = ta.macd(data['Close'])
        data['MACD']        = macd['MACD_12_26_9']
        data['MACDSignal']  = macd['MACDs_12_26_9']

        bb = ta.bbands(data['Close'], length=20)
        data['UpperBB'] = bb['BBU_20_2.0']
        data['LowerBB'] = bb['BBL_20_2.0']

        data['ADX'] = ta.adx(data['High'], data['Low'], data['Close'], length=14)['ADX_14']

        stoch = ta.stoch(data['High'], data['Low'], data['Close'])
        data['StochK'] = stoch['STOCHk_14_3_3']
        data['StochD'] = stoch['STOCHd_14_3_3']

        # --- RELATIVE VOLUME (sicher ohne Namenskonflikt) ---
        data['AvgVolume_20'] = data['Volume'].rolling(window=20).mean()
        data['my_rel_volume'] = data['Volume'] / data['AvgVolume_20']

        # Letzte Zeile
        latest = data.iloc[-1]
        rel_vol = latest['my_rel_volume']

        # ==================== FILTER ====================
        if (latest['Close'] > latest['SMA50'] > latest['SMA200'] and      # Uptrend
            latest['RSI'] < 40 and                                        # Übersold
            rel_vol > 1.5 and                                             # Hohes Rel. Volumen
            latest['ATR'] / latest['Close'] > 0.01 and                     # Genug Volatilität
            latest['MACD'] > latest['MACDSignal'] and                     # Bullisches MACD
            latest['Close'] > latest['LowerBB'] and                       # Am unteren BB
            latest['ADX'] > 25 and                                        # Starker Trend
            latest['StochK'] > latest['StochD']):                          # Bullisches Stoch

            return {
                'Ticker': ticker,
                'Close':  round(latest['Close'], 2),
                'RSI':    round(latest['RSI'], 1),
                'RelVol': round(rel_vol, 2),
                'ATR%':   round(latest['ATR']/latest['Close']*100, 2),
                'ADX':    round(latest['ADX'], 1),
            }
        return None

    except Exception as e:
        st.error(f"Fehler bei {ticker}: {e}")
        return None


# ==================== STREAMLIT APP ====================
st.set_page_config(page_title="Swing Scanner", layout="wide")
st.title("Swingtrading Bullish Pullback Scanner")

tickers_input = st.text_area(
    "Ticker (kommagetrennt)",
    value="AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META,JPM,V,MA,UNH,HD,PG,BAC,WFC",
    height=100
)
tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]

if st.button("Scan starten", type="primary"):
    results = []
    progress = st.progress(0)
    
    for i, ticker in enumerate(tickers):
        result = scan_stock(ticker)
        if result:
            results.append(result)
        progress.progress((i + 1) / len(tickers))

    if results:
        df = pd.DataFrame(results)
        st.success(f"{len(df)} Setups gefunden!")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode()
        st.download_button("CSV herunterladen", csv, "swing_setups.csv", "text/csv")
    else:
        st.warning("Keine Setups gefunden – Markt vielleicht gerade zu stark?")

st.caption("Stand: " + datetime.datetime.now().strftime("%d.%m.%Y %H:%M"))
