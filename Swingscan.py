# ==================== STREAMLIT APP – ALLE S&P 500 ====================
import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

# ==================== FESTE S&P 100 LISTE (kein Web-Scraping!) ====================
SP100_TICKERS = [
    "AAPL","MSFT","GOOGL","GOOG","AMZN","NVDA","META","TSLA","BRK-B","JPM",
    "UNH","V","MA","LLY","HD","PG","JNJ","XOM","AVGO","MRK","ABBV","CVX",
    "KO","PEP","COST","ADBE","TMO","CRM","AMD","NFLX","ACN","LIN","MCD",
    "ABT","CSCO","DIS","TMUS","WFC","TXN","QCOM","AMGN","INTU","NOW",
    "IBM","PM","UNP","HON","GE","CAT","RTX","NEE","GS","SBUX","BKNG",
    "MDT","LMT","GILD","ISRG","SPGI","BMY","ELV","SYK","ADP","AXP","T",
    "VRTX","REGN","PGR","PLD","BLK","CB","AMT","SCHW","CI","DE","MO",
    "BA","MDLZ","MMC","KLAC","SO","DUK","ZTS","ICE","SHW","ITW","CL",
    "LRCX","BSX","CME","TGT","EOG","BDX","APH","PNC","EMR","FDX","MSI",
    "NSC","HUM","ANET","CSX","WM","ORLY","MCO","ECL","AZO"
]

# ==================== STREAMLIT APP ====================
st.set_page_config(page_title="S&P 100 Swing Scanner", layout="wide")
st.title("Swingtrading Bullish Pullback Scanner – S&P 100")

scan_mode = st.radio("Scan-Modus", ["S&P 100 (100 Top-Aktien)", "Eigene Liste"])

if scan_mode == "S&P 100 (100 Top-Aktien)":
    tickers = SP100_TICKERS
    st.info(f"S&P 100 geladen → {len(tickers)} Aktien")
else:
    tickers_input = st.text_area("Ticker (kommagetrennt)", height=120)
    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]

if st.button("Scan starten", type="primary"):
    with st.spinner(f"Scanne {len(tickers)} Aktien..."):
        results = []
        progress = st.progress(0)
        for i, ticker in enumerate(tickers):
            result = scan_stock(ticker)
            if result:
                results.append(result)
            progress.progress((i + 1) / len(tickers))

        if results:
            df = pd.DataFrame(results)
            st.success(f"{len(df)} Bullish Pullback Setups gefunden!")
            st.dataframe(df.sort_values("RSI"), use_container_width=True)
            csv = df.to_csv(index=False).encode()
            st.download_button("CSV herunterladen", csv, "sp100_setups.csv", "text/csv")
        else:
            st.info("Heute keine Setups im S&P 100 – Markt ist sehr stark oder sehr schwach.")
