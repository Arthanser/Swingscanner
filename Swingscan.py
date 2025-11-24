import streamlit as st
import yfinance as yf
import pandas as pd
import talib
import datetime

# Funktion zum Scannen einer einzelnen Aktie (aus deinem vorherigen Code)
def scan_stock(ticker, period='1y', interval='1d'):
    try:
        data = yf.download(ticker, period=period, interval=interval)
        if data.empty:
            return None
        
        # Indikatoren berechnen
        data['SMA50'] = talib.SMA(data['Close'], timeperiod=50)
        data['SMA200'] = talib.SMA(data['Close'], timeperiod=200)
        data['RSI'] = talib.RSI(data['Close'], timeperiod=14)
        data['AvgVolume'] = data['Volume'].rolling(window=20).mean()
        data['RelVolume'] = data['Volume'] / data['AvgVolume']
        data['ATR'] = talib.ATR(data['High'], data['Low'], data['Close'], timeperiod=14)
        data['MACD'], data['MACDSignal'], _ = talib.MACD(data['Close'])
        data['UpperBB'], data['MiddleBB'], data['LowerBB'] = talib.BBANDS(data['Close'], timeperiod=20)
        data['ADX'] = talib.ADX(data['High'], data['Low'], data['Close'], timeperiod=14)
        data['StochK'], data['StochD'] = talib.STOCH(data['High'], data['Low'], data['Close'])
        
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
                # Füge weitere Werte hinzu, falls gewünscht
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