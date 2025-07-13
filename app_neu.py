import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Studiengangs-Matching", page_icon="🎓", layout="wide")

# ----------------- Styling -----------------
st.markdown("""
<style>
    .match-card {
        background-color: #f9f9f9;
        padding: 1rem;
        border-radius: 1rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .match-high { color: green; font-weight: bold; font-size: 1.1em; }
    .match-medium { color: orange; font-weight: bold; font-size: 1.1em; }
    .match-low { color: red; font-weight: bold; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# ----------------- Initialisierung -----------------
def init_state():
    if 'page' not in st.session_state:
        st.session_state.page = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'zusatz' not in st.session_state:
        st.session_state.zusatz = {}
    if 'ergebnis_seite' not in st.session_state:
        st.session_state.ergebnis_seite = 0

# ----------------- Daten laden -----------------
@st.cache_data
def lade_fragen():
    return pd.read_csv("fragebogen_kurzversion.csv", sep=";")

@st.cache_data
def lade_studiengaenge():
    df = pd.read_csv("Zuordnung_Studium_Beruf_Vollständig_MOTIVIERT.csv", sep="\t")
    return df

# ----------------- Fragebogen -----------------
def fragebogen_seite():
    fragen = lade_fragen()
    items_pro_seite = 10
    max_seiten = (len(fragen) + items_pro_seite - 1) // items_pro_seite + 1

    st.progress((st.session_state.page + 1) / max_seiten)

    if st.session_state.page < max_seiten - 1:
        start = st.session_state.page * items_pro_seite
        end = min(start + items_pro_seite, len(fragen))

        for idx in range(start, end):
            frage = fragen.iloc[idx]
            antwort = st.radio(
                frage['Frage'],
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: ["Gar nicht", "Wenig", "Teils", "Stark", "Sehr stark"][x-1],
                key=f"frage_{idx}",
                horizontal=True
            )
            st.session_state.answers[idx] = {
                "dimension": frage['Zuordnung'],
                "reverse": frage['Reverse'],
                "wert": 6 - antwort if frage['Reverse'] == 1 else antwort
            }
    elif st.session_state.page == max_seiten - 1:
        with st.expander("Zusatzfragen", expanded=False):
            st.session_state.zusatz['motivation'] = st.selectbox(
                "Was motiviert dich bei der Studienwahl am meisten?",
                ["Persönliche Leidenschaft", "Berufsaussichten", "Gesellschaftlicher Beitrag"]
            )
            st.session_state.zusatz['umgebung'] = st.selectbox(
                "In welcher Arbeitsumgebung fühlst du dich am wohlsten?",
                ["Labor/Werkstatt", "Büro", "Mit Menschen", "Kreativ", "Draußen"]
            )

    col1, col2 = st.columns([1, 1])
    if st.session_state.page > 0:
        if col1.button("← Zurück"):
            st.session_state.page -= 1
            st.rerun()
    if st.session_state.page < max_seiten - 1:
        if col2.button("Weiter →"):
            st.session_state.page += 1
            st.rerun()
    else:
        if col2.button("Auswertung", type="primary"):
            st.session_state.page = 'results'
            st.rerun()

# ----------------- Profilberechnung -----------------
def berechne_profil():
    werte = {}
    zähler = {}
    for a in st.session_state.answers.values():
        dim = a['dimension']
        werte[dim] = werte.get(dim, 0) + a['wert']
        zähler[dim] = zähler.get(dim, 0) + 1
    return {k: werte[k]/zähler[k] for k in werte}

# ----------------- Matching -----------------
def berechne_match(profil, zeile):
    dims = profil.keys()
    abweichung = np.mean([abs(profil[d] - 3) for d in dims])
    score = max(0, 100 - abweichung * 20)

    if st.session_state.zusatz['motivation'] == "Berufsaussichten" and str(zeile.get("Arbeitsmarktbedarf", "")).lower() == "sehr hoch":
        score *= 1.1

    return min(score, 100)

# ----------------- Ergebnisse -----------------
def ergebnisse_seite():
    st.header("📊 Deine Studiengangs-Empfehlungen")

    profil = berechne_profil()
    df = lade_studiengaenge()
    df['Match'] = df.apply(lambda row: berechne_match(profil, row), axis=1)
    df = df.sort_values('Match', ascending=False)

    st.subheader("🧠 Dein Persönlichkeitsprofil")
    for dim in sorted(profil):
        filled = int(round(profil[dim]))
        bar = "🟦" * filled + "⬜" * (5 - filled)
        st.write(f"**{dim}**: {bar} ({profil[dim]:.1f}/5)")

    st.subheader("🎯 Studiengänge passend zu deinem Profil")
    seite = st.session_state.ergebnis_seite
    anzahl_pro_seite = 10
    start = seite * anzahl_pro_seite
    end = start + anzahl_pro_seite
    top = df.iloc[start:end]

    for _, row in top.iterrows():
        studiengang = row.get('Studiengang', 'Unbekannt')
        match = row.get('Match', 0)

        with st.container():
            st.markdown(f"<div class='match-card'>", unsafe_allow_html=True)
            st.markdown(f"### 🎓 {studiengang} — Match: {match:.0f}%")
            st.write(f"**📌 NC:** {row.get('NC', 'k.A.')}")
            st.write(f"**💰 Einstiegsgehalt:** {row.get('Einstiegsgehalt', 'k.A.')} €")
            st.write(f"**💼 Berufsfelder:** {row.get('Berufsfelder TOP3', 'k.A.')}")
            st.write(f"**📈 Arbeitsmarktbedarf:** {row.get('Arbeitsmarktbedarf', 'k.A.')}")
            st.write(f"**🪙 Einstiegsspanne:** {row.get('Einstieg spanne', 'k.A.')}")
            st.write(f"**📊 Gehalt nach 5 Jahren:** {row.get('Gehalt nach 5 Jahren', 'k.A.')}")

            if match >= 80:
                st.markdown("<p class='match-high'>✨ Sehr gute Übereinstimmung</p>", unsafe_allow_html=True)
            elif match >= 60:
                st.markdown("<p class='match-medium'>👍 Gute Übereinstimmung</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p class='match-low'>🤔 Mäßige Übereinstimmung</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    if seite > 0:
        if col1.button("← Zurück", key="zurueck"):
            st.session_state.ergebnis_seite -= 1
            st.rerun()
    if end < len(df):
        if col2.button("Mehr anzeigen →", key="weiter"):
            st.session_state.ergebnis_seite += 1
            st.rerun()

    if st.button("🔄 Neuer Durchlauf"):
        st.session_state.clear()
        st.rerun()

# ----------------- Hauptprogramm -----------------
def haupt():
    init_state()
    if st.session_state.page == 'results':
        ergebnisse_seite()
    else:
        fragebogen_seite()

if __name__ == "__main__":
    haupt()
