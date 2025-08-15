import streamlit as st
import requests

## T

API_BASE = "https://daily-python-script.onrender.com"
API_LEAGUES = f"{API_BASE}/leagues"

st.set_page_config(page_title="BPM Selector", layout="wide")

# --- HEADER E TITOLO ---
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🎯 BPM - Selettore Chicchette</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- SELEZIONE CAMPIONATO ---
with st.sidebar:
    st.header("⚽ Seleziona il Campionato")

    try:
        response = requests.get(API_LEAGUES)
        response.raise_for_status()
        leagues = response.json().get("leagues", [])
        leagues = [league.replace("_", " ").title() for league in leagues]
        leagues.sort()

        selected_league = st.selectbox("Campionato", leagues)
    except Exception as e:
        st.error(f"Errore nel caricamento delle leghe: {e}")
        selected_league = None

# --- MAIN SECTION ---
if selected_league:
    st.success(f"Hai selezionato: **{selected_league.replace('_', ' ').title()}**")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Squadre e Statistiche (prossimo step)")

        # Qui potrai in futuro visualizzare le squadre
        st.info("Elenco squadre e bottone analisi...")

    with col2:
        st.subheader("📝 Log analisi o dettagli")
        st.code("Risultati dell'analisi... verranno mostrati qui", language="text")
else:
    st.warning("Seleziona un campionato dal menu a sinistra.")





# import streamlit as st
# import requests
# import urllib.parse

# API_BASE = "https://daily-python-script.onrender.com"
# API_LEAGUES = f"{API_BASE}/leagues"
# API_TEAMS = f"{API_BASE}/teams/"
# API_STATS = f"{API_BASE}/stats/"

# st.set_page_config(page_title="BPM - Selettore Chicchette", layout="centered")
# st.title("⚽ BPM - Chicchette Selector")

# # --- Carica le leghe ---
# @st.cache_data
# def carica_leghe():
#     try:
#         response = requests.get(API_LEAGUES)
#         response.raise_for_status()
#         leagues = response.json().get("leagues", [])
#         return sorted(leagues)
#     except Exception as e:
#         st.error(f"Errore nel caricamento delle leghe: {e}")
#         return []

# leagues = carica_leghe()
# lega_selezionata = st.selectbox("Seleziona il Campionato", leagues)

# # --- Carica le squadre ---
# def get_teams(lega):
#     try:
#         response = requests.get(f"{API_TEAMS}{lega}")
#         response.raise_for_status()
#         return sorted(response.json().get("teams", []))
#     except Exception as e:
#         st.error(f"Errore nel caricamento squadre: {e}")
#         return []

# teams = []
# if lega_selezionata:
#     teams = get_teams(lega_selezionata)

# # --- Analisi di tutte le squadre ---
# def analizza_squadra(team, lega):
#     league_encoded = urllib.parse.quote(lega)
#     team_encoded = urllib.parse.quote(team)

#     url = f"{API_STATS}{league_encoded}/{team_encoded}"
#     try:
#         response = requests.get(url)
#         if response.status_code != 200:
#             return f"❌ {team} - Errore {response.status_code}"

#         data = response.json()
#         matches = data.get("matches", [])
#         if not matches:
#             return f"ℹ️ {team}: Nessuna partita trovata."

#         message = ""
#         match_count = len(matches)
#         scored = 0
#         conceded = 0
#         consecutivi_non_segna = 0
#         max_non_segna = 0
#         consecutivi_non_subisce = 0
#         max_non_subisce = 0
#         win = lose = draw = 0

#         matches = matches[::-1]  # Ordina dalla più recente

#         for match in matches:
#             home = match["home_team"]
#             away = match["away_team"]
#             fthg = match["fthg"]
#             ftag = match["ftag"]

#             is_home = (team == home)
#             is_away = (team == away)

#             if (is_home and fthg > ftag) or (is_away and ftag > fthg):
#                 win += 1
#             elif (is_home and fthg < ftag) or (is_away and ftag < fthg):
#                 lose += 1
#             else:
#                 draw += 1

#             if is_home:
#                 scored += fthg
#                 conceded += ftag
#             else:
#                 scored += ftag
#                 conceded += fthg

#             # Non segna
#             if (is_home and fthg == 0) or (is_away and ftag == 0):
#                 consecutivi_non_segna += 1
#                 max_non_segna = max(max_non_segna, consecutivi_non_segna)
#             else:
#                 consecutivi_non_segna = 0

#             # Non subisce
#             if (is_home and ftag == 0) or (is_away and fthg == 0):
#                 consecutivi_non_subisce += 1
#                 max_non_subisce = max(max_non_subisce, consecutivi_non_subisce)
#             else:
#                 consecutivi_non_subisce = 0

#         message += f"\n**{team}**\n- Partite giocate: {match_count}\n- Fatti: {scored} | Subiti: {conceded}\n- W: {win} | L: {lose} | D: {draw}\n"

#         if consecutivi_non_segna > 0:
#             message += f"  - Non segna da {consecutivi_non_segna} (Max: {max_non_segna})\n"
#         if consecutivi_non_subisce > 0:
#             message += f"  - Non subisce da {consecutivi_non_subisce} (Max: {max_non_subisce})\n"

#         if consecutivi_non_segna == max_non_segna and max_non_segna > 0:
#             message += f"  ⚠ Mai più di {max_non_segna} partite senza segnare\n"
#         if consecutivi_non_subisce == max_non_subisce and max_non_subisce > 0:
#             message += f"  ⚠ Mai più di {max_non_subisce} clean sheet\n"

#         return message
#     except Exception as e:
#         return f"❌ Errore durante analisi {team}: {e}"

# # --- Avvia analisi su tutte le squadre ---
# if teams and st.button("Avvia la ricerca su tutte le squadre"):
#     with st.spinner("Analisi in corso..."):
#         for idx, team in enumerate(teams):
#             st.markdown(analizza_squadra(team, lega_selezionata))
#         st.success("Analisi completata!")
