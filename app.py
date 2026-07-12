import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configurazione Pagina Mobile-Responsive
st.set_page_config(page_title="ETF Analytics Private", page_icon="📈", layout="wide")

# --- SICUREZZA ---
# Inserisci qui la tua password personalizzata
PASSWORD_SEGRETA = "9117" 

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

# --- APPLICAZIONE ANALYTICS ---
st.title("📈 ETF Real-Time Analytics")
st.caption("Strumento privato ottimizzato per PC e Android")

ticker_input = st.text_input("Inserisci il Ticker dell'ETF (es. SPY, QQQ, SWDA.MI):", "").strip().upper()

if ticker_input:
    with st.spinner(f"Estrazione dati per {ticker_input} in corso..."):
        try:
            # Inizializzazione ticker ticker
            ticker = yf.Ticker(ticker_input)
            
            # Scarica 1 anno di dati storici giornalieri per indicatori tecnici
            df = ticker.history(period="1y")
            
            # Scarica i dati in tempo reale (info)
            info = ticker.info
            
            if df.empty:
                st.error("Nessun dato storico trovato per questo ticker. Controlla la sintassi.")
                st.stop()
                
            # --- 1. DATI DI PREZZO E SPREAD ---
            prezzo_attuale = df['Close'].iloc[-1]
            
            # Gestione Spread Bid/Ask (Spesso N/A su ETF Europei)
            bid = info.get('bid')
            ask = info.get('ask')
            if bid and ask and bid > 0 and ask > 0:
                spread = ask - bid
                spread_pct = (spread / ask) * 100
                spread_str = f"{spread:.4f} ({spread_pct:.2f}%)"
            else:
                spread_str = "N/A (Dato non disponibile)"
                
            # --- 2. VOLUMI ---
            volume_odierno = df['Volume'].iloc[-1]
            volume_30g = df['Volume'].tail(30).mean()
            
            # --- 3. CALCOLO INDICATORI TECNICI (Puro Pandas) ---
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
            
            # Segnale MACD
            if macd_attuale > signal_attuale:
                indicatore_macd = "🟢 RIALZISTA (MACD sopra Signal Line)"
            else:
                indicatore_macd = "🔴 RIBASSISTA (MACD sotto Signal Line)"
                
            # --- 4. CALCOLO PUT-CALL RATIO STABILE ---
            put_call_ratio_str = "N/A (Nessuna opzione liquida)"
            try:
                scadenze = ticker.options
                if scadenze:
                    # Analizza la prima scadenza disponibile per massima stabilità e velocità
                    opzioni = ticker.option_chain(scadenze[0])
                    vol_calls = opzioni.calls['volume'].sum()
                    vol_puts = opzioni.puts['volume'].sum()
                    
                    if vol_calls > 0 and vol_puts > 0:
                        pcr = vol_puts / vol_calls
                        put_call_ratio_str = f"{pcr:.2f}"
            except:
                pass # Lascia N/A in caso di formati anomali o mercati chiusi
                
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

# Pulsante di Logout rapido per sicurezza su Mobile
if st.button("Chiudi Sessione (Lock)"):
    st.session_state["autenticato"] = False
    st.rerun()
