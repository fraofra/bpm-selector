# import streamlit as st
import requests
import urllib.parse

# --- API ---
API_BASE = "https://daily-python-script.onrender.com"
API_LEAGUES = f"{API_BASE}/leagues"
API_TEAMS = f"{API_BASE}/teams/"
API_STATS = f"{API_BASE}/stats/"

# --- CONFIG ---
st.set_page_config(page_title="🎯 BPM - Selettore Chicchette", layout="centered")

# --- HEADER ---
st.markdown(
    """
    <h1 style='text-align: center; color: #FF5722;'>🎯 BPM - Selettore di Chicchette</h1>
    <p style='text-align: center; font-size:18px;'>Scova i trend più succosi nei campionati minori... o anche nei più strani 😎</p>
    <hr>
    """, unsafe_allow_html=True
)

# --- FUNZIONI ---
@st.cache_data
def carica_leghe():
    try:
        response = requests.get(API_LEAGUES)
        response.raise_for_status()
        return sorted(response.json().get("leagues", []))
    except Exception as e:
        st.error(f"❌ Errore nel caricamento delle leghe: {e}")
        return []

def get_teams(lega):
    try:
        response = requests.get(f"{API_TEAMS}{lega}")
        response.raise_for_status()
        return sorted(response.json().get("teams", []))
    except Exception as e:
        st.error(f"❌ Errore nel caricamento squadre: {e}")
        return []

def analizza_squadra(team, lega):
    league_encoded = urllib.parse.quote(lega)
    team_encoded = urllib.parse.quote(team)
    url = f"{API_STATS}{league_encoded}/{team_encoded}"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return f"❌ {team} - Errore {response.status_code}"

        data = response.json()
        matches = data.get("matches", [])
        if not matches:
            return f"ℹ️ {team}: Nessuna partita trovata."

        match_count = len(matches)
        scored = conceded = 0
        consecutivi_non_segna = max_non_segna = 0
        consecutivi_non_subisce = max_non_subisce = 0
        win = lose = draw = 0

        matches = matches[::-1]  # Ordine cronologico

        for match in matches:
            home = match["home_team"]
            away = match["away_team"]
            fthg = match["fthg"]
            ftag = match["ftag"]
            is_home = (team == home)

            goals_for = fthg if is_home else ftag
            goals_against = ftag if is_home else fthg
            scored += goals_for
            conceded += goals_against

            # Risultato
            if goals_for > goals_against:
                win += 1
            elif goals_for < goals_against:
                lose += 1
            else:
                draw += 1

            # Non segna
            if goals_for == 0:
                consecutivi_non_segna += 1
                max_non_segna = max(max_non_segna, consecutivi_non_segna)
            else:
                consecutivi_non_segna = 0

            # Non subisce
            if goals_against == 0:
                consecutivi_non_subisce += 1
                max_non_subisce = max(max_non_subisce, consecutivi_non_subisce)
            else:
                consecutivi_non_subisce = 0

        msg = f"""
        ### 📊 {team}
        - Partite giocate: **{match_count}**
        - ⚽ Gol fatti: **{scored}** | 🛡️ Subiti: **{conceded}**
        - 🟢 Vittorie: {win} | 🔴 Sconfitte: {lose} | 🟡 Pareggi: {draw}
        """

        if max_non_segna > 0:
            msg += f"\n- 😬 Massimo senza segnare: {max_non_segna} partite"
        if max_non_subisce > 0:
            msg += f"\n- 🧱 Massimo clean sheet consecutivi: {max_non_subisce}"

        return msg

    except Exception as e:
        return f"❌ Errore analisi {team}: {e}"

# --- UI: SCELTA LEGA ---
leagues = carica_leghe()
lega_selezionata = st.selectbox("📍 Scegli il campionato da esplorare", leagues)

teams = get_teams(lega_selezionata) if lega_selezionata else []

# --- BUTTON ---
if teams:
    if st.button("🔍 Lancia la Scansione Chicchette!"):
        with st.spinner("💡 Caricamento delle magie..."):
            for team in teams:
                st.markdown(analizza_squadra(team, lega_selezionata))
            st.balloons()
            st.success("🎉 Analisi completata! Hai trovato qualcosa di interessante?")
