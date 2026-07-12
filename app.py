import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

# Configurazione Pagina Mobile-Responsive
st.set_page_config(page_title="ETF Analytics Private", page_icon="📈", layout="wide")

# --- SICUREZZA ---
PASSWORD_SEGRETA = "Render26!" 

if "autenticato" not in st.session_state:
    st.session_state["autenticato"] = False

if not st.session_state["autenticato"]:
    st.title("🔒 Accesso Riservato")
    password_input = st.text_input("Inserisci il PIN di sblocco:", type="password")
    if st.button("Accedi"):
        if password_input == PASSWORD_SEGRETA:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("PIN errato. Accesso negato.")
    st.stop()

# --- PATCH ANTI-BLOCCO PER YFINANCE ---
# Creiamo una sessione HTTP con uno User-Agent reale per evitare il blocco di Yahoo Finance
@st.cache_resource
def get_secure_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    return session

sessione_protetta = get_secure_session()

# --- APPLICAZIONE ANALYTICS ---
st.title("📈 ETF Real-Time Analytics")
st.caption("Strumento privato ottimizzato per PC e Android")

ticker_input = st.text_input("Inserisci il Ticker dell'ETF (es. SPY, QQQ, WNUC.DE, SWDA.MI):", "").strip().upper()

if ticker_input:
    with st.spinner(f"Estrazione dati sicura per {ticker_input}..."):
        try:
            # Inizializzazione ticker agganciando la sessione camuffata da browser reale
            ticker = yf.Ticker(ticker_input, session=sessione_protetta)
            
            # Scarica 1 anno di dati storici giornalieri (endpoint solido e difficilmente bloccabile)
            df = ticker.history(period="1y")
            
            if df.empty:
                st.error("Nessun dato trovato. Verifica che il ticker sia corretto su Yahoo Finance.")
                st.stop()
                
            # --- 1. DATI DI PREZZO ---
            prezzo_attuale = df['Close'].iloc[-1]
            
            # --- 2. GESTIONE SPREAD BID/ASK SENZA USARE TICKER.INFO ---
            # Cerchiamo di estrarre lo spread dai dati rapidi 'fast_info' per evitare il crash di ticker.info
            spread_str = "N/A (Dato non disponibile)"
            try:
                # Alcuni ticker supportano fast_info, proviamo a estrarre in modo sicuro
                fast_info = ticker.fast_info
                bid = fast_info.get('bid', None)
                ask = fast_info.get('ask', None)
                if bid and ask and bid > 0 and ask > 0:
                    spread = ask - bid
                    spread_pct = (spread / ask) * 100
                    spread_str = f"{spread:.4f} ({spread_pct:.2f}%)"
            except:
                pass # Rimane N/A se fast_info fallisce o non ha i campi bid/ask
                
            # --- 3. VOLUMI ---
            volume_odierno = df['Volume'].iloc[-1]
            volume_30g = df['Volume'].tail(30).mean()
            
            # --- 4. CALCOLO INDICATORI TECNICI (Puro Pandas locale, nessun rischio crash) ---
            # Medie Mobili
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['MA200'] = df['Close'].rolling(window=200).mean()
            ma50_val = df['MA50'].iloc[-1]
            ma200_val = df['MA200'].iloc[-1]
            
            # RSI (14 periodi)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_val = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MACD (12, 26, 9)
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            
            macd_attuale = macd_line.iloc[-1]
            signal_attuale = signal_line.iloc[-1]
            
            if macd_attuale > signal_attuale:
                indicatore_macd = "🟢 RIALZISTA (MACD sopra Signal Line)"
            else:
                indicatore_macd = "🔴 RIBASSISTA (MACD sotto Signal Line)"
                
            # --- 5. CALCOLO PUT-CALL RATIO PROTETTO ---
            put_call_ratio_str = "N/A (Nessuna opzione liquida)"
            try:
                scadenze = ticker.options
                if scadenze:
                    opzioni = ticker.option_chain(scadenze[0])
                    vol_calls = opzioni.calls['volume'].sum()
                    vol_puts = opzioni.puts['volume'].sum()
                    
                    if vol_calls > 0 and vol_puts > 0:
                        pcr = vol_puts / vol_calls
                        put_call_ratio_str = f"{pcr:.2f}"
            except:
                pass # Rimane N/A se la catena delle opzioni è protetta o assente
                
            # --- VISUALIZZAZIONE INTERFACCIA METRICS ---
            st.markdown(f"### Target Analizzato: **{ticker_input}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Prezzo Attuale", f"{prezzo_attuale:.2f}")
                st.metric("RSI (14)", f"{rsi_val:.2f}")
                st.metric("Put-Call Ratio", put_call_ratio_str)
                
            with col2:
                st.metric("Volume Odierno", f"{volume_odierno:,.0f}")
                st.metric("Volume Medio (30g)", f"{volume_30g:,.0f}")
                st.metric("Spread Bid/Ask", spread_str)
                
            with col3:
                st.metric("MA 50", f"{ma50_val:.2f}" if not pd.isna(ma50_val) else "N/A")
                st.metric("MA 200", f"{ma200_val:.2f}" if not pd.isna(ma200_val) else "N/A")
                st.write("**Stato MACD:**")
                st.markdown(f"**{indicatore_macd}**")

        except Exception as e:
            st.error(f"Errore durante l'elaborazione del ticker. Dettaglio: {e}")

# Pulsante di Logout rapido
if st.button("Chiudi Sessione (Lock)"):
    st.session_state["autenticato"] = False
    st.rerun()
