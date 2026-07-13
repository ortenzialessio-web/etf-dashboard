# ETF Financial Dashboard 📈

Questa è un'applicazione web interattiva scritta in Python con **Streamlit** e **Plotly** per l'analisi tecnica in tempo reale di ETF (Exchange-Traded Funds).

La pagina è progettata per essere privata ed è protetta da password, rendendola ideale per la consultazione personale da PC o Android.

## Funzionalità Principali

Visualizza e analizza in tempo reale per qualsiasi ticker ETF:
1. **Prezzo Attuale & Variazione Giornaliera**: Calcolato dall'ultimo prezzo disponibile.
2. **Spread Bid/Ask**: Mostra i prezzi di acquisto/vendita e calcola lo spread in valore assoluto e percentuale (indicatore di liquidità).
3. **Volume Giornaliero & Media 30 Giorni**: Per valutare la partecipazione istituzionale.
4. **Put-Call Ratio (PCR)**: Basato sul volume e open interest delle opzioni (per ETF con opzioni disponibili).
5. **Medie Mobili (MA50 & MA200)**: Identifica il trend a medio e lungo termine (Golden Cross / Death Cross).
6. **RSI (Relative Strength Index)**: Identifica situazioni di ipercomprato (>70) o ipervenduto (<30).
7. **MACD (Moving Average Convergence Divergence)**: Indicatore di momentum con trend rialzista/ribassista.
8. **Grafici Interattivi Plotly**: Zoomabili e responsive su dispositivi mobili.
9. **Descrizioni Finanziarie**: Spiegazioni e guide all'interpretazione in italiano integrate per ogni metrica.

---

## Come Avviare l'Applicazione in Locale

Segui questi passaggi sul tuo computer (PC):

1. **Prerequisiti**: Assicurati di avere Python 3.11 installato (funziona anche con versioni superiori come Python 3.14).
2. **Installa le dipendenze**:
   Apri il terminale nella cartella del progetto ed esegui:
   ```bash
   pip install -r requirements.txt
   ```
3. **Imposta la tua Password Privata** (Opzionale):
   Di default, l'applicazione usa la password `admin123`. Puoi impostare la tua password personalizzata tramite variabile d'ambiente:
   - **Windows PowerShell**:
     ```powershell
     $env:DASHBOARD_PASSWORD="tua_password_sicura"
     ```
   - **Windows CMD**:
     ```cmd
     set DASHBOARD_PASSWORD=tua_password_sicura
     ```
   - **Linux / macOS**:
     ```bash
     export DASHBOARD_PASSWORD="tua_password_sicura"
     ```
4. **Avvia Streamlit**:
   ```bash
   streamlit run streamlit_app.py
   ```
5. **Accedi da Android/PC**:
   - Da PC: apri il browser all'indirizzo locale mostrato nel terminale (solitamente `http://localhost:8501`).
   - Da Android (nella stessa rete locale Wi-Fi): apri l'indirizzo IP locale del tuo PC con la porta `8501` (es. `http://192.168.1.50:8501`). In alternativa, vedi sotto per deployare l'app su Internet.

---

## Come Distribuire su Render (Gratuito e Privato)

Per vedere la pagina ovunque ti trovi dal tuo telefono Android o PC senza che il tuo PC debba rimanere acceso:

### Passo 1: Carica il codice su GitHub
1. Crea un nuovo repository **privato** sul tuo account GitHub (es. `etf-dashboard`).
2. Esegui il push di questa cartella nel tuo repository:
   ```bash
   git init
   git add .
   git commit -m "First commit: ETF Dashboard"
   git branch -M main
   git remote add origin https://github.com/TUO_USERNAME/etf-dashboard.git
   git push -u origin main
   ```

### Passo 2: Configura Render
1. Accedi a [Render](https://render.com) ed effettua il login (magari con GitHub).
2. Clicca su **New +** e seleziona **Web Service**.
3. Collega il tuo account GitHub e seleziona il repository privato `etf-dashboard`.
4. Configura i dettagli del Web Service:
   - **Name**: `etf-dashboard` (o qualsiasi nome desideri)
   - **Region**: Scegli quella più vicina a te (es. Frankfurt)
   - **Branch**: `main`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run streamlit_app.py --server.port $PORT`
5. Scorri in basso, apri la sezione **Advanced** ed inserisci le seguenti **Environment Variables**:
   - `DASHBOARD_PASSWORD`: Imposta la tua password personalizzata (es. `lamiaetfpass2026`). Questa sarà la password da inserire per accedere.
   - `PYTHON_VERSION`: `3.11.9` (Render scaricherà e utilizzerà automaticamente Python 3.11 come richiesto).
6. Clicca su **Deploy Web Service**.

Una volta completato il deploy, Render ti fornirà un link pubblico tipo `https://etf-dashboard.onrender.com`. Solo tu potrai accedere al pannello inserendo la password che hai configurato!
