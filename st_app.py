import streamlit as st
import requests
import urllib.parse
from datetime import datetime
from math import exp, factorial

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
    lega_txt = lega.replace("_"," ").title()

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
            # st.session_state.alert_list.append(f"{team} non segna da {consecutivi_non_segna} (Max: {max_non_segna})\n")
        if consecutivi_non_subisce > 0:
            message += f"  - Non subisce da {consecutivi_non_subisce} (Max: {max_non_subisce})\n"
            # st.session_state.alert_list.append(f"{team} non subisce da {consecutivi_non_subisce} (Max: {max_non_subisce})\n")

        if consecutivi_non_segna == max_non_segna and max_non_segna > 0:
            message += f"\n ⚠️ Mai più di {max_non_segna} partite senza segnare\n"
            st.session_state.alert_list.append(f"{lega_txt} - {team}\n ⚠️ Limite non segna ({max_non_segna} in {match_count} partite)\n")
        if consecutivi_non_subisce == max_non_subisce and max_non_subisce > 0:
            message += f"\n ⚠️ Mai più di {max_non_subisce} clean sheet\n"
            st.session_state.alert_list.append(f"{lega_txt} - {team}\n ⚠️ Limite non subisce ({max_non_subisce} in {match_count} partite)\n")

        return message
    except Exception as e:
        return f"❌ Errore durante analisi {team}: {e}"


def poisson(k, lam):
    """Probabilità Poisson per k eventi con media lam"""
    return (lam ** k) * exp(-lam) / factorial(k)

def calcola_quote_poisson(home_team, away_team, campionato):
    # Recupero info dal tuo sistema (presumo già connesso a DB)
    home_info = get_info(home_team, campionato)
    away_info = get_info(away_team, campionato)

    if not home_info or not away_info:
        return "Dati insufficienti."

    # Media gol segnati da casa / subiti da away
    avg_home_goals = home_info[1] / home_info[0]       # tot gol fatti in casa / partite
    avg_away_conceded = away_info[2] / away_info[0]    # tot gol subiti fuori / partite
    expected_home_goals = round((avg_home_goals + avg_away_conceded) / 2, 2)

    # Media gol segnati da away / subiti da casa
    avg_away_goals = away_info[1] / away_info[0]       # tot gol fatti fuori
    avg_home_conceded = home_info[2] / home_info[0]    # tot gol subiti in casa
    expected_away_goals = round((avg_away_goals + avg_home_conceded) / 2, 2)

    # Costruzione matrice Poisson
    max_goals = 5
    matrix = []
    for i in range(max_goals + 1):
        row = []
        for j in range(max_goals + 1):
            p = poisson(i, expected_home_goals) * poisson(j, expected_away_goals)
            row.append(p)
        matrix.append(row)

    # Calcola prob Over 2.5
    over_2_5 = sum(matrix[i][j] for i in range(6) for j in range(6) if i + j > 2)
    under_2_5 = 1 - over_2_5
    quote_over = round(1 / over_2_5, 2)
    quote_under = round(1 / under_2_5, 2)

    

    # Risultato esatto più probabile
    max_prob = 0
    risultato_probabile = ""
    for i in range(6):
        for j in range(6):
            if matrix[i][j] > max_prob:
                max_prob = matrix[i][j]
                risultato_probabile = f"{i}-{j}"

    top_risultati = sorted(
        [(i, j, matrix[i][j]) for i in range(6) for j in range(6)],
        key=lambda x: x[2], reverse=True
    )[:5]

    ris_list=[]
    
    for r in top_risultati:
        ris_list.append(f"🔸 {r[0]}-{r[1]} ({r[2]*100:.1f}%)")
        # print(f"- {r[0]}-{r[1]} ({r[2]*100:.1f}%)")
    risulta_piu= "\n".join(ris_list)
    # Calcola probabilità BTS (entrambe segnano)
    bts_prob = sum(
        matrix[i][j]
        for i in range(1, 6)
        for j in range(1, 6)
    )
    no_bts_prob = 1 - bts_prob
    quote_bts = round(1 / bts_prob, 2)
    quote_no_bts = round(1 / no_bts_prob, 2)

    risultato = ""
    # campionato_txt = campionato.replace("_"," ").title()
    risultato += f"\n📊 Gol attesi: {expected_home_goals} - {expected_away_goals}\n"
    risultato += f"\n📈 Over 2.5: {over_2_5*100:.2f}% → quota: {quote_over}\n"
    risultato += f"\n📉 Under 2.5: {under_2_5*100:.2f}% → quota: {quote_under}\n"
    risultato += f"\n🤝 Entrambe a segno: {bts_prob*100:.2f}% → quota: {quote_bts}\n"
    risultato += f"\n🚫 No Goal: {no_bts_prob*100:.2f}% → quota: {quote_no_bts}\n"
    risultato += f"\n🎯 Risultato più probabile: {risultato_probabile} ({max_prob*100:.1f}%)\n"
    risultato += f"\n{risulta_piu}\n"   

    return risultato    

def get_info(team, lega):
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
        scored = 0
        conceded = 0
       

        matches = matches[::-1]  # Ordina dalla più recente

        for match in matches:
            home = match["home_team"]
            away = match["away_team"]
            fthg = match["fthg"]
            ftag = match["ftag"]

            is_home = (team == home)
            is_away = (team == away)


            if is_home:
                scored += fthg
                conceded += ftag
            else:
                scored += ftag
                conceded += fthg

        return match_count, scored, conceded
    except Exception as e:
        return f"❌ Errore durante analisi {team}: {e}"

# --- Avvia analisi su tutte le squadre ---
if teams and st.button("Avvia la ricerca sul campionato"):
    with st.spinner("Analisi in corso..."):
        for idx, team in enumerate(teams):
            st.markdown(analizza_squadra(team, lega_selezionata.replace(" ","_").lower()))
        st.success("Analisi completata!")

if st.button("📊 Analizza le partite di oggi"):
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




if st.button("📋 Quote di oggi"):
    partite = get_partite_oggi()

    if partite:
        st.subheader("Quote di oggi (clicca per espandere)")

        partite.sort(key=lambda x: x["ora"].split()[-1])  # Ordina per orario

        for match in partite:
            home = match["home_team"]
            away = match["away_team"]
            orario = match["ora"].split()[-1]
            campionato = match["league"]
            campionato_nome = campionato.replace("_", " ").title()

            titolo = f"⚽ {orario} - {campionato_nome}: {home} vs {away}"
            key_match_p = f"{home}_{away}_{orario.replace(':','')}"

            if key_match_p not in st.session_state:
                st.session_state[key_match_p] = False

            with st.expander(titolo):
                # Se ancora non analizzato, esegui analisi
                if not st.session_state[key_match_p]:
                    with st.spinner("Analisi in corso..."):
                        try:
                            home_analysis = calcola_quote_poisson(home, away, campionato)
                        except:
                            continue
                        st.session_state[f"{key_match_p}_home"] = home_analysis

                        st.session_state[key_match_p] = True  # Flag per evitare riesecuzione

                # Mostra analisi già fatte
                st.markdown(f"{home} - {away}")
                st.markdown(st.session_state.get(f"{key_match_p}_home", "Nessun dato"))


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
        st.info("Nessun alert generato oggi.. analizza le partite")