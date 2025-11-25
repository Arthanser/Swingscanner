# ==================== STREAMLIT APP – ALLE S&P 500 ====================
import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(page_title="Swing Scanner – Alle Märkte", layout="wide")
st.title("Swingtrading Bullish Pullback Scanner – Alle US-Aktien")

# Liste der S&P 500 Ticker automatisch laden
@st.cache_data(ttl=86400)  # einmal pro Tag neu laden
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url)[0]
    return table['Symbol'].str.replace('.', '-', regex=False).tolist()

# Optionen
scan_mode = st.radio("Was möchtest du scannen?", 
                     ["S&P 500 (ca. 500 Aktien)", "Nasdaq-100", "Meine eigene Liste"])

if scan_mode == "Meine eigene Liste":
    tickers_input = st.text_area("Ticker (kommagetrennt)", height=120)
    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
else:
    with st.spinner("Lade Aktienliste..."):
        if scan_mode == "S&P 500 (ca. 500 Aktien)":
            tickers = get_sp500_tickers()
            st.info(f"S&P 500 geladen → {len(tickers)} Aktien")
        elif scan_mode == "Nasdaq-100":
            ndx = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")[4]
            tickers = ndx['Ticker'].tolist()
            st.info(f"Nasdaq-100 geladen → {len(tickers)} Aktien")

if st.button("Scan starten – alle Aktien durchsuchen", type="primary"):
    with st.spinner(f"Scanne {len(tickers)} Aktien – kann 30–90 Sekunden dauern..."):
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
            st.download_button("CSV herunterladen", csv, "swing_setups.csv", "text/csv")
        else:
            st.info("Heute keine Setups – Markt ist zu stark oder zu schwach. Morgen wieder versuchen!")

st.caption(f"Stand: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
