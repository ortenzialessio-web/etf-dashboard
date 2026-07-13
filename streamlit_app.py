import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="ETF Dashboard Privata",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZZATO PER ESTETICA PREMIUM ---
st.markdown("""
<style>
    /* Importa font Outfit da Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
            /* Sfondo nero per l'intera app */
.stApp {
    background-color: #000000;
}

/* Sfondo nero anche per la sidebar */
[data-testid="stSidebar"] {
    background-color: #0a0a0a;
}
            
    /* Titoli Principali con Gradiente */
    .main-title {
        background: linear-gradient(135deg, #00C6FF, #0072FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.8rem;
        margin-bottom: 0.2rem;
        text-shadow: 0px 4px 20px rgba(0, 198, 255, 0.15);
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #FFFFFF !important;
        margin-bottom: 2rem;
    }
    
    /* Box metriche premium con effetto vetro (glassmorphism) */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        margin-bottom: 15px;
        transition: transform 0.2s ease-in-out, border-color 0.2s ease-in-out;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 198, 255, 0.3);
    }
    
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #90CDF4;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1.2;
    }
    
    .metric-delta {
        font-size: 0.9rem;
        margin-top: 5px;
        font-weight: 600;
    }
    
    .delta-positive {
        color: #48BB78;
    }
    
    .delta-negative {
        color: #F56565;
    }
    
    .delta-neutral {
        color: #FFFFFF !important;
    }
    
    /* Stile personalizzato per gli expander descrittivi */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    
    /* Login container */
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        text-align: center;
    }
            
    /* --- FORZATURA GLOBALE TESTO BIANCO --- */
    /* Copre tutto il testo "di default" generato da Streamlit
       (paragrafi, span, liste, label, caption, sidebar, tab, expander)
       che altrimenti resta grigio scuro (colore di default del tema chiaro). */
    .stApp, .stApp p, .stApp span, .stApp li, .stApp label,
    .stApp div, .stMarkdown, .stMarkdown p,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] *,
    [data-testid="stTabs"] p,
    [data-testid="stExpander"] p,
    .streamlit-expanderHeader p {
        color: #FFFFFF !important;
    }
    
    /* Ripristiniamo i colori specifici che NON devono diventare bianchi */
    .delta-positive, .delta-positive * { color: #48BB78 !important; }
    .delta-negative, .delta-negative * { color: #F56565 !important; }
    .metric-title, .metric-title * { color: #90CDF4 !important; }
    .main-title { -webkit-text-fill-color: transparent !important; }        
</style>
""", unsafe_allow_html=True)

# --- AUTENTICAZIONE ---
def check_password():
    """Restituisce True se l'utente ha inserito la password corretta."""
    # Recupera la password corretta dalle variabili d'ambiente o usa quella di default
    CORRECT_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "admin123")
    
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Se non autenticato, mostra il form di login
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://img.icons8.com/gradient/100/security-checked.png", width=70)
    st.markdown("<h2 style='margin-top:15px; color:#FFFFFF;'>Accesso Riservato</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#FFFFFF !important; font-size:0.9rem;'>Questa dashboard è privata. Inserisci la password per continuare.</p>", unsafe_allow_html=True)
    
    password_input = st.text_input("Password", type="password", key="login_password_field", label_visibility="collapsed")
    submit_button = st.button("Accedi", use_container_width=True)
    
    if submit_button or password_input:
        if password_input == CORRECT_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("🔑 Password non corretta. Riprova.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    return False

# --- LOGICA DI CALCOLO INDICATORI ---

def calculate_rsi(prices, period=14):
    """Calcola il Relative Strength Index (RSI) con smoothing di Wilder."""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices):
    """Calcola il MACD, Signal Line e Istogramma."""
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

def get_put_call_ratio(ticker):
    """Estrae il Put-Call Ratio dalla catena di opzioni per la scadenza più vicina."""
    try:
        options = ticker.options
        if not options:
            return None, None, "Opzioni non disponibili (nessuna scadenza trovata)"
        
        # Consideriamo la scadenza più vicina
        nearest_expiry = options[0]
        opt = ticker.option_chain(nearest_expiry)
        
        calls = opt.calls
        puts = opt.puts
        
        # Somma volumi e Open Interest (gestendo eventuali NaN e colonne mancanti)
        call_vol = float(calls['volume'].fillna(0).sum()) if 'volume' in calls.columns else 0
        put_vol = float(puts['volume'].fillna(0).sum()) if 'volume' in puts.columns else 0
        
        call_oi = float(calls['openInterest'].fillna(0).sum()) if 'openInterest' in calls.columns else 0
        put_oi = float(puts['openInterest'].fillna(0).sum()) if 'openInterest' in puts.columns else 0
        
        pcr_vol = put_vol / call_vol if call_vol > 0 else None
        pcr_oi = put_oi / call_oi if call_oi > 0 else None
        
        info_msg = f"Dati basati sulla scadenza opzioni più vicina: {nearest_expiry}"
        return pcr_vol, pcr_oi, info_msg
    except Exception as e:
        return None, None, f"Non disponibile per questo ticker (Borsa non USA o opzioni non liquide)"

# --- PROCEDI SE AUTENTICATO ---
if check_password():
    
    # --- SIDEBAR E CONFIGURAZIONE UTENTE ---
    with st.sidebar:
        st.markdown("<h3 style='color:#FFFFFF; margin-bottom:10px;'>⚙️ Impostazioni</h3>", unsafe_allow_html=True)
        
        # Input ticker
        ticker_input = st.text_input("Ticker ETF (es. SPY, QQQ, SWDA.MI)", value="SPY").strip().upper()
        
        # Selezione orizzonte temporale
        timeframe_options = {
            "3 Mesi": 90,
            "6 Mesi": 180,
            "1 Anno": 365,
            "2 Anni": 730,
            "5 Anni": 1825
        }
        selected_tf_label = st.selectbox("Orizzonte temporale grafico", list(timeframe_options.keys()), index=2)
        days_to_display = timeframe_options[selected_tf_label]
        
        st.markdown("---")
        
        # Informazioni di debug / Info utili
        st.markdown("""
        **Suggerimenti ticker:**
        - `SPY` (S&P 500 USA)
        - `QQQ` (Nasdaq 100 USA)
        - `SWDA.MI` (MSCI World UCITS Milano)
        - `EIMI.AS` (Emerging Markets UCITS Amsterdam)
        """)
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()
            
    # --- ACQUISIZIONE DATI ---
    if ticker_input:
        ticker = yf.Ticker(ticker_input)
        
        with st.spinner(f"Scaricamento dati in corso per {ticker_input}..."):
            # Scarichiamo 2 anni extra per calcolare MA200 e indicatori tecnici accuratamente
            # anche se l'utente richiede un grafico a 3 mesi.
            download_days = max(days_to_display + 300, 750) 
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=download_days)
            
            # Scarica lo storico
            hist = ticker.history(start=start_date, end=end_date)
            
            # Scarica le informazioni in tempo reale (bid, ask, info generali)
            # yfinance può dare errori o rallentamenti con .info, lo gestiamo
            try:
                info = ticker.info
            except Exception:
                info = {}

        if hist.empty:
            st.error(f"❌ Impossibile trovare dati storici per il ticker '{ticker_input}'. Verifica che sia corretto ed esista su Yahoo Finance.")
        else:
            # Calcolo indicatori sull'intero dataset
            hist['MA50'] = hist['Close'].rolling(window=50).mean()
            hist['MA200'] = hist['Close'].rolling(window=200).mean()
            hist['RSI'] = calculate_rsi(hist['Close'], period=14)
            macd_line, signal_line, macd_hist = calculate_macd(hist['Close'])
            hist['MACD_Line'] = macd_line
            hist['MACD_Signal'] = signal_line
            hist['MACD_Hist'] = macd_hist
            hist['Vol_MA30'] = hist['Volume'].rolling(window=30).mean()
            
            # Filtriamo il dataframe per visualizzare solo il periodo richiesto dall'utente
            df_display = hist.tail(days_to_display)
            
            # Estrazione metriche correnti (ultimo giorno)
            current_row = hist.iloc[-1]
            prev_row = hist.iloc[-2] if len(hist) > 1 else current_row
            
            price_current = current_row['Close']
            price_change = price_current - prev_row['Close']
            price_change_pct = (price_change / prev_row['Close']) * 100
            
            # Valore valuta
            currency = info.get('currency', 'USD')
            
            # Dettagli Bid/Ask
            bid = info.get('bid')
            ask = info.get('ask')
            
            # Volume
            vol_current = current_row['Volume']
            vol_avg_30 = current_row['Vol_MA30']
            
            # MA50 & MA200 attuali
            ma50_current = current_row['MA50']
            ma200_current = current_row['MA200']
            
            # RSI attuale
            rsi_current = current_row['RSI']
            
            # MACD attuale
            macd_current = current_row['MACD_Line']
            macd_sig_current = current_row['MACD_Signal']
            macd_hist_current = current_row['MACD_Hist']
            macd_trend = "Rialzista 🟢" if macd_current > macd_sig_current else "Ribassista 🔴"
            
            # Put-Call Ratio
            pcr_vol, pcr_oi, pcr_info = get_put_call_ratio(ticker)
            
            # --- INTESTAZIONE DASHBOARD ---
            etf_name = info.get('longName', ticker_input)
            st.markdown(f'<h1 class="main-title">{ticker_input} - {etf_name}</h1>', unsafe_allow_html=True)
            st.markdown(f'<p class="subtitle">Analisi tecnica in tempo reale • Valuta: {currency} • Aggiornato al: {current_row.name.strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)
            
            # --- SEZIONE METRICHE PRINCIPALI (RIGA 1) ---
            col1, col2, col3, col4 = st.columns(4)
            
            # Card Prezzo
            with col1:
                sign = "+" if price_change >= 0 else ""
                delta_class = "delta-positive" if price_change >= 0 else "delta-negative"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Prezzo Attuale</div>
                    <div class="metric-value">{price_current:.2f} {currency}</div>
                    <div class="metric-delta {delta_class}">{sign}{price_change:.2f} ({sign}{price_change_pct:.2f}%) oggi</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Card Spread Bid/Ask
            with col2:
                if bid and ask:
                    spread = abs(ask - bid)
                    spread_pct = (spread / ask) * 100 if ask > 0 else 0
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Spread Bid / Ask</div>
                        <div class="metric-value">{spread:.4f} {currency}</div>
                        <div class="metric-delta delta-neutral">Bid: {bid:.2f} | Ask: {ask:.2f} ({spread_pct:.3f}%)</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Spread Bid / Ask</div>
                        <div class="metric-value">N/D</div>
                        <div class="metric-delta delta-neutral">Dati bid/ask in tempo reale non disponibili</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Card Volume
            with col3:
                vol_ratio = (vol_current / vol_avg_30) * 100 if vol_avg_30 > 0 else 100
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Volume Giornaliero</div>
                    <div class="metric-value">{vol_current:,.0f}</div>
                    <div class="metric-delta delta-neutral">Media 30g: {vol_avg_30:,.0f} ({vol_ratio:.1f}%)</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Card Put-Call Ratio (PCR)
            with col4:
                if pcr_vol is not None:
                    pcr_status = "Rialzista (poche put)" if pcr_vol < 0.7 else ("Ribassista (molte put)" if pcr_vol > 1.0 else "Neutrale")
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Put-Call Ratio (Vol)</div>
                        <div class="metric-value">{pcr_vol:.2f}</div>
                        <div class="metric-delta delta-neutral">OI PCR: {pcr_oi:.2f} ({pcr_status})</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Put-Call Ratio</div>
                        <div class="metric-value">N/D</div>
                        <div class="metric-delta delta-neutral">Nessuna opzione quotata o liquida</div>
                    </div>
                    """, unsafe_allow_html=True)

            # --- SEZIONE METRICHE TECNICHE (RIGA 2) ---
            col_tech1, col_tech2, col_tech3 = st.columns(3)
            
            # Card Medie Mobili
            with col_tech1:
                if pd.notna(ma50_current) and pd.notna(ma200_current):
                    status_ma = "Golden Cross ⚡" if price_current > ma50_current > ma200_current else (
                        "Bearish Cross ⚠️" if price_current < ma50_current < ma200_current else "Trend Misto"
                    )
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Medie Mobili (MA)</div>
                        <div class="metric-value">MA50: {ma50_current:.2f}</div>
                        <div class="metric-delta delta-neutral">MA200: {ma200_current:.2f} | {status_ma}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Medie Mobili (MA)</div>
                        <div class="metric-value">Calcolo...</div>
                        <div class="metric-delta delta-neutral">Dati storici insufficienti per MA200</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            # Card RSI
            with col_tech2:
                if pd.notna(rsi_current):
                    rsi_status = "Ipercomprato 🔴" if rsi_current > 70 else ("Ipervenduto 🟢" if rsi_current < 30 else "Neutrale ⚪")
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">RSI (14 Giorni)</div>
                        <div class="metric-value">{rsi_current:.2f}</div>
                        <div class="metric-delta delta-neutral">Segnale: {rsi_status}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">RSI (14 Giorni)</div>
                        <div class="metric-value">N/D</div>
                        <div class="metric-delta delta-neutral">Calcolo in corso...</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            # Card MACD
            with col_tech3:
                if pd.notna(macd_current):
                    macd_color_class = "delta-positive" if macd_current > macd_sig_current else "delta-negative"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">MACD (12, 26, 9)</div>
                        <div class="metric-value">{macd_current:.3f}</div>
                        <div class="metric-delta {macd_color_class}">Trend MACD: {macd_trend}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">MACD (12, 26, 9)</div>
                        <div class="metric-value">N/D</div>
                        <div class="metric-delta delta-neutral">Calcolo in corso...</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")

            # --- GRAFICI INTERATTIVI (PLOTLY) ---
            st.markdown("### 📊 Grafici Finanziari Interattivi")
            
            # Layout tab per non affollare la pagina su dispositivi mobili (Android)
            tab_price, tab_rsi, tab_macd, tab_volume = st.tabs([
                "📈 Prezzo & Medie Mobili", 
                "📉 RSI (Forza Relativa)", 
                "📊 MACD Trend", 
                "🔊 Volumi Scambiati"
            ])
            
            # Tab 1: Prezzo e Medie Mobili
            with tab_price:
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=df_display.index, y=df_display['Close'],
                    mode='lines', name='Prezzo Chiusura',
                    line=dict(color='#00C6FF', width=2.5)
                ))
                if 'MA50' in df_display.columns:
                    fig_price.add_trace(go.Scatter(
                        x=df_display.index, y=df_display['MA50'],
                        mode='lines', name='MA 50',
                        line=dict(color='#FF9F43', width=1.5, dash='dash')
                    ))
                if 'MA200' in df_display.columns:
                    fig_price.add_trace(go.Scatter(
                        x=df_display.index, y=df_display['MA200'],
                        mode='lines', name='MA 200',
                        line=dict(color='#EE5253', width=1.5, dash='dot')
                    ))
                
                fig_price.update_layout(
                    title=f"Prezzo Storico di {ticker_input} con Medie Mobili (50 e 200 giorni)",
                    template="plotly_dark",
                    height=500,
                    xaxis_title="Data",
                    yaxis_title=f"Prezzo ({currency})",
                    margin=dict(l=40, r=40, t=60, b=40),
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_price, use_container_width=True)
                
                # Descrizione educazionale
                st.info("""
                **📈 Descrizione Prezzo & Medie Mobili (MA50 & MA200):**
                - **Prezzo Attuale**: Il valore dell'ultimo scambio registrato sul mercato.
                - **Media Mobile 50 giorni (MA50)**: Rappresenta il trend a medio termine dell'ETF.
                - **Media Mobile 200 giorni (MA200)**: Rappresenta il trend a lungo termine. 
                - **Segnale Operativo**: Quando il prezzo è sopra la MA200, il mercato è in un trend rialzista di lungo termine. L'incrocio al rialzo della MA50 sopra la MA200 è chiamato **Golden Cross** (segnale fortemente rialzista), mentre il contrario è un **Death Cross** (segnale ribassista).
                """)

            # Tab 2: RSI
            with tab_rsi:
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(
                    x=df_display.index, y=df_display['RSI'],
                    mode='lines', name='RSI (14)',
                    line=dict(color='#9b59b6', width=2)
                ))
                # Linee di soglia ipercomprato/ipervenduto
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="#e74c3c", annotation_text="Ipercomprato (70)", annotation_position="top left")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="#2ecc71", annotation_text="Ipervenduto (30)", annotation_position="bottom left")
                
                fig_rsi.update_layout(
                    title="RSI (Relative Strength Index) - Indice di Forza Relativa a 14 Giorni",
                    template="plotly_dark",
                    height=400,
                    xaxis_title="Data",
                    yaxis_title="RSI",
                    yaxis=dict(range=[10, 90]),
                    margin=dict(l=40, r=40, t=60, b=40),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_rsi, use_container_width=True)
                
                # Descrizione
                st.info("""
                **📉 Descrizione RSI (Relative Strength Index):**
                L'RSI è un oscillatore di momentum che misura la velocità e la variazione dei movimenti di prezzo su una scala da 0 a 100.
                - **Ipercomprato (> 70)**: L'ETF potrebbe essere sopravvalutato nel breve termine ed è probabile un ritracciamento o consolidamento del prezzo.
                - **Ipervenduto (< 30)**: L'ETF potrebbe essere sottovalutato ed è probabile un rimbalzo tecnico.
                - **Zona Neutrale (30-70)**: Il trend del prezzo è stabile senza eccessi.
                """)

            # Tab 3: MACD
            with tab_macd:
                fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                          vertical_spacing=0.08, row_heights=[0.7, 0.3])
                
                # Linee MACD e Segnale
                fig_macd.add_trace(go.Scatter(
                    x=df_display.index, y=df_display['MACD_Line'],
                    mode='lines', name='MACD Line', line=dict(color='#00C6FF', width=2)
                ), row=1, col=1)
                
                fig_macd.add_trace(go.Scatter(
                    x=df_display.index, y=df_display['MACD_Signal'],
                    mode='lines', name='Signal Line', line=dict(color='#ff7675', width=1.5, dash='dash')
                ), row=1, col=1)
                
                # Istogramma con colori dinamici (verde per positivo, rosso per negativo)
                colors = ['#2ecc71' if val >= 0 else '#e74c3c' for val in df_display['MACD_Hist']]
                fig_macd.add_trace(go.Bar(
                    x=df_display.index, y=df_display['MACD_Hist'],
                    name='Istogramma', marker_color=colors
                ), row=2, col=1)
                
                fig_macd.update_layout(
                    title="MACD (Moving Average Convergence Divergence) e Istogramma",
                    template="plotly_dark",
                    height=500,
                    margin=dict(l=40, r=40, t=60, b=40),
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_macd, use_container_width=True)
                
                # Descrizione
                st.info("""
                **📊 Descrizione MACD (Moving Average Convergence Divergence):**
                Il MACD è un indicatore di trend-following (inseguitore di trend) che mostra la relazione tra due medie mobili esponenziali (EMA a 12 e 26 periodi).
                - **MACD Line**: La differenza tra le due EMA.
                - **Signal Line**: La media mobile esponenziale a 9 periodi del MACD stesso.
                - **Trend Rialzista (Bullish)**: Si verifica quando la MACD Line attraversa al rialzo la Signal Line (istogramma verde). Indica momentum in aumento.
                - **Trend Ribassista (Bearish)**: Si verifica quando la MACD Line attraversa al ribasso la Signal Line (istogramma rosso). Indica momentum in calo.
                """)

            # Tab 4: Volumi
            with tab_volume:
                fig_vol = go.Figure()
                
                # Volumi con colore dinamico
                vol_colors = []
                for i in range(len(df_display)):
                    # Se il prezzo di chiusura è salito rispetto al giorno precedente, volume verde, altrimenti rosso
                    if i == 0:
                        vol_colors.append('#2ecc71')
                    else:
                        prev_close = df_display['Close'].iloc[i-1]
                        curr_close = df_display['Close'].iloc[i]
                        vol_colors.append('#2ecc71' if curr_close >= prev_close else '#e74c3c')
                
                fig_vol.add_trace(go.Bar(
                    x=df_display.index, y=df_display['Volume'],
                    name='Volume Giornaliero', marker_color=vol_colors, opacity=0.7
                ))
                
                if 'Vol_MA30' in df_display.columns:
                    fig_vol.add_trace(go.Scatter(
                        x=df_display.index, y=df_display['Vol_MA30'],
                        mode='lines', name='Media Mobile Volumi (30g)',
                        line=dict(color='#f1c40f', width=2)
                    ))
                
                fig_vol.update_layout(
                    title="Volume degli Scambi Giornalieri e Media Mobile a 30 Giorni",
                    template="plotly_dark",
                    height=450,
                    xaxis_title="Data",
                    yaxis_title="Numero di Quote Scambiate",
                    margin=dict(l=40, r=40, t=60, b=40),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_vol, use_container_width=True)
                
                # Descrizione
                st.info("""
                **🔊 Descrizione Volume & Volume Medio 30 giorni:**
                - **Volume**: Rappresenta il numero totale di quote o azioni dell'ETF scambiate nell'arco della giornata di borsa.
                - **Media Mobile 30 giorni (Vol_MA30)**: Rappresenta il livello normale o atteso di scambi per questo specifico strumento.
                - **Interpretazione**: Volumi significativamente superiori alla media a 30 giorni durante forti rialzi o ribassi confermano la forza del movimento in corso (alta partecipazione degli investitori istituzionali). Volumi bassi indicano indecisione o scarso interesse.
                """)

            # Sezione aggiuntiva per il Put-Call Ratio
            st.markdown("---")
            st.markdown("### 🔍 Approfondimento Put-Call Ratio & Spread Bid/Ask")
            col_pcr_desc, col_spread_desc = st.columns(2)
            
            with col_pcr_desc:
                st.markdown("""
                **📉 Put-Call Ratio (PCR):**
                Il PCR misura il volume di contratti di opzioni Put acquistate rispetto alle opzioni Call. 
                - **Significato**: Le Put sono coperture o scommesse ribassiste, le Call sono scommesse rialziste.
                - **Valori chiave**: 
                  - Un PCR **inferiore a 0.7** indica forte ottimismo (rialzista, molte Call rispetto alle Put).
                  - Un PCR **superiore a 1.0** indica timore o pessimismo (ribassista, molte Put rispetto alle Call).
                - *Nota: Negli ETF UCITS europei i dati delle opzioni potrebbero non essere disponibili su Yahoo Finance poiché non hanno mercati di opzioni standardizzati o accessibili via API.*
                """)
                if pcr_info:
                    st.caption(f"ℹ️ {pcr_info}")
                
            with col_spread_desc:
                st.markdown("""
                **💸 Spread Bid / Ask:**
                Lo spread rappresenta la differenza tra il miglior prezzo d'acquisto (Bid) e il miglior prezzo di vendita (Ask) quotati sul book.
                - **Costo di Transazione Implicito**: Uno spread stretto (basso in % e valore assoluto) indica un mercato liquido e costi di transazione minimi per te. Uno spread ampio indica minore liquidità.
                - **Interpretazione**: Gli ETF altamente scambiati (es. SPY) hanno spread vicini allo 0.01% o meno, mentre gli ETF specializzati o europei in orari di chiusura USA possono avere spread superiori.
                """)
                if bid and ask:
                    st.success(f"La liquidità attuale per questo ETF è buona con uno spread percentuale dello {((abs(ask-bid)/ask)*100):.4f}% durante l'ultimo scambio.")
                else:
                    st.warning("I dati Bid/Ask non sono disponibili in questo momento (questo accade spesso a mercati chiusi o per ticker quotati fuori dagli Stati Uniti).")
                    
    else:
        st.info("Digita un ticker valido nella barra laterale e premi Invio per avviare l'analisi.")
