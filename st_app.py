import streamlit as st
import requests
import urllib.parse
from datetime import datetime

API_BASE = "https://daily-python-script.onrender.com"
API_LEAGUES = f"{API_BASE}/leagues"
API_TEAMS = f"{API_BASE}/teams/"
API_STATS = f"{API_BASE}/stats/"
if "alert_list" not in st.session_state:
    st.session_state.alert_list = []

st.set_page_config(page_title="BPM - Limited Chicchette", layout="centered")
st.title("⚽ BPM Selector")

# --- Carica le leghe ---
@st.cache_data
def carica_leghe():
    try:
        response = requests.get(API_LEAGUES)
        response.raise_for_status()
        leagues = response.json().get("leagues", [])
        leagues = [league.replace("_"," ").title() for league in leagues]        
        return sorted(leagues)
    except Exception as e:
        st.error(f"Errore nel caricamento delle leghe: {e}")
        return []

leagues = carica_leghe()

lega_selezionata = st.selectbox("Seleziona il Campionato", leagues)


@st.cache_data
def get_partite_oggi():
    try:
        response = requests.get("https://daily-python-script.onrender.com/next")
        response.raise_for_status()
        dati = response.json()
        match_list = dati.get("next_matches", [])

        oggi = datetime.now().strftime("%d.%m.")

        partite_oggi = [
            {
                "home_team": match["home_team"],
                "away_team": match["away_team"],
                "league": match["league"],
                "ora": match["date"]
            }
            for match in match_list
            if match.get("date", "").startswith(oggi)
        ]

        return partite_oggi
    except Exception as e:
        st.error(f"Errore nel recupero delle partite odierne: {e}")
        return []

# --- Carica le squadre ---
def get_teams(lega):
    lega = lega.replace(" ","_").lower()
    try:
        response = requests.get(f"{API_TEAMS}{lega}")
        response.raise_for_status()
        return sorted(response.json().get("teams", []))
    except Exception as e:
        st.error(f"Errore nel caricamento squadre: {e}")
        return []

teams = []
if lega_selezionata:
    teams = get_teams(lega_selezionata)

# --- Analisi di tutte le squadre ---
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

        message = ""
        match_count = len(matches)
        scored = 0
        conceded = 0
        consecutivi_non_segna = 0
        max_non_segna = 0
        consecutivi_non_subisce = 0
        max_non_subisce = 0
        win = lose = draw = 0

        matches = matches[::-1]  # Ordina dalla più recente

        for match in matches:
            home = match["home_team"]
            away = match["away_team"]
            fthg = match["fthg"]
            ftag = match["ftag"]

            is_home = (team == home)
            is_away = (team == away)

            if (is_home and fthg > ftag) or (is_away and ftag > fthg):
                win += 1
            elif (is_home and fthg < ftag) or (is_away and ftag < fthg):
                lose += 1
            else:
                draw += 1

            if is_home:
                scored += fthg
                conceded += ftag
            else:
                scored += ftag
                conceded += fthg

            # Non segna
            if (is_home and fthg == 0) or (is_away and ftag == 0):
                consecutivi_non_segna += 1
                max_non_segna = max(max_non_segna, consecutivi_non_segna)
            else:
                consecutivi_non_segna = 0

            # Non subisce
            if (is_home and ftag == 0) or (is_away and fthg == 0):
                consecutivi_non_subisce += 1
                max_non_subisce = max(max_non_subisce, consecutivi_non_subisce)
            else:
                consecutivi_non_subisce = 0

        message += f"\n**{team}**\n- Partite giocate: {match_count}\n- Fatti: {scored} | Subiti: {conceded}\n- W: {win} | L: {lose} | D: {draw}\n"

        if consecutivi_non_segna > 0:
            message += f"  - Non segna da {consecutivi_non_segna} (Max: {max_non_segna})\n"
            st.session_state.alert_list.append(f"{team} non segna da {consecutivi_non_segna} (Max: {max_non_segna})\n")
        if consecutivi_non_subisce > 0:
            message += f"  - Non subisce da {consecutivi_non_subisce} (Max: {max_non_subisce})\n"
            st.session_state.alert_list.append(f"{team} non subisce da {consecutivi_non_subisce} (Max: {max_non_subisce})\n")

        if consecutivi_non_segna == max_non_segna and max_non_segna > 0:
            message += f"\n ⚠ Mai più di {max_non_segna} partite senza segnare\n"
            st.session_state.alert_list.append(f"{team} ⚠ Mai più di {max_non_segna} partite senza segnare\n")
        if consecutivi_non_subisce == max_non_subisce and max_non_subisce > 0:
            message += f"\n ⚠ Mai più di {max_non_subisce} clean sheet\n"
            st.session_state.alert_list.append(f"{team} ⚠ Mai più di {max_non_subisce} partite senza subire\n")

        return message
    except Exception as e:
        return f"❌ Errore durante analisi {team}: {e}"

# --- Avvia analisi su tutte le squadre ---
if teams and st.button("Avvia la ricerca su tutte le squadre"):
    with st.spinner("Analisi in corso..."):
        for idx, team in enumerate(teams):
            st.markdown(analizza_squadra(team, lega_selezionata.replace(" ","_").lower())
        st.success("Analisi completata!")

if st.button("Analizza le partite di oggi"):
    st.session_state.alert_list = []  # ✅ resetta gli alert all'avvio
    partite = get_partite_oggi()

    if partite:
        st.subheader("📋 Partite di oggi (clicca per espandere)")

        partite.sort(key=lambda x: x["ora"].split()[-1])  # Ordina per orario

        for match in partite:
            home = match["home_team"]
            away = match["away_team"]
            orario = match["ora"].split()[-1]
            campionato = match["league"]
            campionato_nome = campionato.replace("_", " ").title()

            titolo = f"⚽ {orario} - {campionato_nome}: {home} vs {away}"
            key_match = f"{home}_{away}_{orario.replace(':','')}"

            if key_match not in st.session_state:
                st.session_state[key_match] = False

            with st.expander(titolo):
                # Se ancora non analizzato, esegui analisi
                if not st.session_state[key_match]:
                    with st.spinner("Analisi in corso..."):
                        home_analysis = analizza_squadra(home, campionato)
                        away_analysis = analizza_squadra(away, campionato)
                        st.session_state[f"{key_match}_home"] = home_analysis
                        st.session_state[f"{key_match}_away"] = away_analysis
                        st.session_state[key_match] = True  # Flag per evitare riesecuzione

                # Mostra analisi già fatte
                st.markdown(f"{home}")
                st.markdown(st.session_state.get(f"{key_match}_home", "Nessun dato"))

                st.markdown(f"{away}")
                st.markdown(st.session_state.get(f"{key_match}_away", "Nessun dato"))

        st.info("ℹ️ Analisi eseguita alla prima espansione.")
    else:
        st.info("🕊️ Nessuna partita in programma per oggi.")

# --- Mostra alert di oggi ---
if "show_alerts" not in st.session_state:
    st.session_state.show_alerts = False

if st.button("📣 Mostra Alert di Oggi"):
    st.session_state.show_alerts = True  # ✅ Ricorda che vogliamo vedere gli alert

if st.session_state.show_alerts:
    if st.session_state.alert_list:
        st.subheader("⚠️ Alert generati oggi")
        for alert in st.session_state.alert_list:
            st.markdown(f"- {alert}")
    else:
        st.info("Nessun alert generato oggi.")

