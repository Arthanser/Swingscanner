import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import datetime

def scan_stock(ticker, period='1y', interval='1d'):
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data.empty or len(data) < 200:
            return None

        # --- Indikatoren mit Sicherheits-Checks ---
        data['SMA50']  = ta.sma(data['Close'], length=50)
        data['SMA200'] = ta.sma(data['Close'], length=200)
        data['RSI']    = ta.rsi(data['Close'], length=14)

        # MACD
        macd = ta.macd(data['Close'])
        if macd is None or macd.empty:
            return None
        data['MACD']       = macd['MACD_12_26_9']
        data['MACDSignal'] = macd['MACDs_12_26_9']

        # Bollinger Bands
        bb = ta.bbands(data['Close'], length=20)
        if bb is None or bb.empty:
            return None
        data['LowerBB'] = bb['BBL_20_2.0']

        # ADX
        adx_data = ta.adx(data['High'], data['Low'], data['Close'], length=14)
        if adx_data is None or adx_data.empty:
            return None
        data['ADX'] = adx_data['ADX_14']

        # Stochastic
        stoch = ta.stoch(data['High'], data['Low'], data['Close'])
        if stoch is None or stoch.empty:
            return None
        data['StochK'] = stoch['STOCHk_14_3_3']
        data['StochD'] = stoch['STOCHd_14_3_3']

        # ATR
        data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'], length=14)
        if data['ATR'].isna().all():
            return None

        # Relative Volume (sicher)
        data['AvgVolume_20'] = data['Volume'].rolling(window=20).mean()
        data['my_rel_volume'] = data['Volume'] / data['AvgVolume_20']

        latest = data.iloc[-1]
        rel_vol = latest['my_rel_volume']

        # --- Nur wenn alle Werte gültig sind ---
        if pd.isna(latest[['SMA50','SMA200','RSI','MACD','MACDSignal','LowerBB','ADX','StochK','StochD','ATR']]).any():
            return None

        # ==================== FILTER ====================
        if (latest['Close'] > latest['SMA50'] > latest['SMA200'] and
            latest['RSI'] < 50 and
            rel_vol > 1.2 and
            latest['ATR'] / latest['Close'] > 0.01 and
            latest['MACD'] > latest['MACDSignal'] and
            latest['Close'] > latest['LowerBB'] and
            latest['ADX'] > 20 and
            latest['StochK'] > latest['StochD']):

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
        # st.error(f"Fehler bei {ticker}: {e}")   # auskommentiert für saubere Optik
        return None


# ==================== STREAMLIT APP ====================
st.set_page_config(page_title="Swing Scanner", layout="wide")
st.title("Swingtrading Bullish Pullback Scanner")

tickers_input = st.text_area(
    "Ticker (kommagetrennt)",
    value="TSLA,NVDA,META,AMD,SMCI,COIN,HOOD,PLTR,CRWD,ARM,UBER,AFRM,MARA,RIOT,SHOP,SNOW,ZS,NET,PATH,GTLB",
    height=100
)

tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]

if st.button("Scan starten", type="primary"):
    with st.spinner(f"Scanne {len(tickers)} Aktien..."):
        results = []
        for ticker in tickers:
            result = scan_stock(ticker)
            if result:
                results.append(result)

        if results:
            df = pd.DataFrame(results)
            st.success(f"{len(df)} Bullish Pullback Setups gefunden!")
            st.dataframe(df.sort_values("RSI"), use_container_width=True)
            csv = df.to_csv(index=False).encode()
            st.download_button("CSV herunterladen", csv, "swing_setups.csv", "text/csv")
        else:
            st.info("Aktuell keine Setups – vielleicht später nochmal scannen?")

st.caption(f"Stand: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
