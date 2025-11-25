import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta  # Ersetzt TA-Lib – einfacher für Cloud
import datetime

# Funktion zum Scannen einer einzelnen Aktie
def scan_stock(ticker, period='1y', interval='1d'):
    try:
        data = yf.download(ticker, period=period, interval=interval)
        if data.empty:
            return None
        
        # Indikatoren berechnen mit pandas_ta
        data['SMA50'] = ta.sma(data['Close'], length=50)
        data['SMA200'] = ta.sma(data['Close'], length=200)
        data['RSI'] = ta.rsi(data['Close'], length=14)
       # Relative Volume sicher berechnen (vermeidet pandas-ta-Konflikt)
        data['AvgVolume'] = data['Volume'].rolling(window=20).mean()
        data['RelVolume_temp'] = data['Volume'] / data['AvgVolume']      # temporäre Spalte
        data['RelVolume'] = data['RelVolume_temp']                       # jetzt sauber zuweisen
        data = data.drop(columns=['RelVolume_temp'])                     # temp-Spalte wieder löschen
        data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'], length=14)
        macd_data = ta.macd(data['Close'])
        data['MACD'] = macd_data['MACD_12_26_9']
        data['MACDSignal'] = macd_data['MACDs_12_26_9']
        bbands = ta.bbands(data['Close'], length=20)
        data['UpperBB'] = bbands['BBU_20_2.0']
        data['MiddleBB'] = bbands['BBM_20_2.0']
        data['LowerBB'] = bbands['BBL_20_2.0']
        data['ADX'] = ta.adx(data['High'], data['Low'], data['Close'], length=14)['ADX_14']
        stoch = ta.stoch(data['High'], data['Low'], data['Close'])
        data['StochK'] = stoch['STOCHk_14_3_3']
        data['StochD'] = stoch['STOCHd_14_3_3']
        
        # Letzter Datensatz
        latest = data.iloc[-1]
        
        # Filterkriterien für Bullish Pullback Setup (anpassen, falls nötig)
        if (latest['Close'] > latest['SMA50'] > latest['SMA200'] and  # Uptrend
            latest['RSI'] < 40 and  # Übersold
            latest['RelVolume'] > 1.5 and  # Hohes Volumen
            latest['ATR'] / latest['Close'] > 0.01 and  # Mindestvolatilität (1%)
            latest['MACD'] > latest['MACDSignal'] and  # Bullish MACD Crossover
            latest['Close'] > latest['LowerBB'] and  # Nah am unteren Bollinger Band
            latest['ADX'] > 25 and  # Starker Trend
            latest['StochK'] > latest['StochD']):  # Bullish Stochastic
            return {
                'Ticker': ticker,
                'Close': round(latest['Close'], 2),
                'RSI': round(latest['RSI'], 2),
                'RelVolume': round(latest['RelVolume'], 2),
                'ATR': round(latest['ATR'], 2),
                'ADX': round(latest['ADX'], 2),
            }
        return None
    except Exception as e:
        st.error(f"Fehler bei {ticker}: {e}")
        return None

# Streamlit App
st.title("Swingtrading Scanner")

# Eingabe für Ticker-Liste
tickers_input = st.text_area("Ticker-Liste (kommagetrennt, z. B. AAPL,MSFT)", "AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META,JPM,V,MA")
tickers = [t.strip() for t in tickers_input.split(',') if t.strip()]

# Scan-Button
if st.button("Scan starten"):
    results = []
    progress_bar = st.progress(0)
    total_tickers = len(tickers)
    
    for i, ticker in enumerate(tickers):
        result = scan_stock(ticker)
        if result:
            results.append(result)
        progress_bar.progress((i + 1) / total_tickers)
    
    df = pd.DataFrame(results)
    if not df.empty:
        st.success(f"{len(df)} passende Setups gefunden!")
        st.dataframe(df, use_container_width=True)  # Interaktive Tabelle
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("CSV herunterladen", csv, "scan_results.csv", "text/csv")
    else:
        st.warning("Keine passenden Setups gefunden.")
