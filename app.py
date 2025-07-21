import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Studiengangs-Matching", page_icon="🎓", layout="wide")

@st.cache_data
def lade_fragen():
    return pd.read_csv("fragebogen_kurzversion_neu.csv", sep=";")

@st.cache_data
def lade_studiengaenge():
    df = pd.read_csv("Zuordnung_Studium_Beruf_Neu.csv", sep=";")
    return df

def init_state():
    if 'page' not in st.session_state:
        st.session_state.page = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'zusatz' not in st.session_state:
        st.session_state.zusatz = {}
    if 'ergebnis_seite' not in st.session_state:
        st.session_state.ergebnis_seite = 0

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
    else:
        with st.expander("Zusatzfragen", expanded=True):
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

def berechne_profil():
    werte = {}
    zähler = {}
    for a in st.session_state.answers.values():
        dim = a['dimension']
        werte[dim] = werte.get(dim, 0) + a['wert']
        zähler[dim] = zähler.get(dim, 0) + 1
    return {k: werte[k]/zähler[k] for k in werte}

def berechne_match(profil, row):
    dims = profil.keys()
    abweichung = np.mean([abs(profil[d] - 3) for d in dims])
    score = max(0, 100 - abweichung * 20)

    motivation = st.session_state.zusatz.get("motivation", "")

    if motivation == "Berufsaussichten":
        if str(row.get("Arbeitsmarktbedarf", "")).lower() == "sehr hoch":
            score *= 1.1

    elif motivation == "Persönliche Leidenschaft":
        score *= 1.15

    elif motivation == "Gesellschaftlicher Beitrag":
        soziale_faktoren = ["Social", "Artistic", "Enterprising"]
        bonus = sum(profil.get(f, 3) - 3 for f in soziale_faktoren) / len(soziale_faktoren)
        score *= 1 + (bonus * 0.05)

    # Extraversion-Anpassung
    extraversion = profil.get("Extraversion", 3)
    if "sozial" in str(row.get("Berufsfelder TOP3", "")).lower() or row.get("Social", "").lower() in ["stark", "sehr stark"]:
        score *= 1 + ((extraversion - 3) * 0.03)

    return min(score, 100)

def ergebnisse_seite():
    st.header("📊 Deine Studiengangs-Empfehlungen")

    profil = berechne_profil()
    df = lade_studiengaenge()
    df['Match'] = df.apply(lambda row: berechne_match(profil, row), axis=1)
    df = df.sort_values('Match', ascending=False)

    st.subheader("🧠 Dein Persönlichkeitsprofil")
st.markdown(beschreibe_profil(profil))
    for dim in sorted(profil):
        filled = int(round(profil[dim]))
        bar = "🟦" * filled + "⬜" * (5 - filled)
        st.write(f"**{dim}**: {bar} ({profil[dim]:.1f}/5)")

    st.subheader("🎯 Studiengänge passend zu deinem Profil")
    seite = st.session_state.ergebnis_seite
    pro_seite = 10
    top = df.iloc[seite * pro_seite : (seite + 1) * pro_seite]

    for _, row in top.iterrows():
        studiengang = row.get('Studiengang', 'Unbekannt')
        match = row.get('Match', 0)
        with st.expander(f"{studiengang} — Match: {match:.0f}%"):
            st.write(f"**📌 NC:** {row.get('NC', 'k.A.')}")
            st.write(f"**💰 Einstiegsgehalt:** {row.get('Einstiegsgehalt', 'k.A.')} €")
            st.write(f"**💼 Berufsfelder:** {row.get('Berufsfelder TOP3', 'k.A.')}")
            st.write(f"**📈 Arbeitsmarktbedarf:** {row.get('Arbeitsmarktbedarf', 'k.A.')}")
            st.write(f"**🪙 Einstiegsspanne:** {row.get('Einstieg spanne', 'k.A.')}")
            st.write(f"**📊 Gehalt nach 5 Jahren:** {row.get('Gehalt nach 5 Jahren', 'k.A.')} €")

    col1, col2 = st.columns(2)
    if seite > 0:
        if col1.button("← Zurück"):
            st.session_state.ergebnis_seite -= 1
            st.rerun()
    if (seite + 1) * pro_seite < len(df):
        if col2.button("Mehr anzeigen →"):
            st.session_state.ergebnis_seite += 1
            st.rerun()

    if st.button("🔄 Neuer Durchlauf"):
        st.session_state.clear()
        st.rerun()

def haupt():
    init_state()
    if st.session_state.page == 'results':
        ergebnisse_seite()
    else:
        fragebogen_seite()

if __name__ == '__main__':
    haupt()


def beschreibe_profil(profil):
    beschreibung = []
    stufen = [(1.0, 2.4, "wenig ausgeprägt"), (2.5, 3.4, "mittel ausgeprägt"),
              (3.5, 4.4, "stark ausgeprägt"), (4.5, 5.0, "sehr stark ausgeprägt")]
    for dim, wert in profil.items():
        for min_val, max_val, text in stufen:
            if min_val <= wert <= max_val:
                beschreibung.append(f"- **{dim}**: {text} ({wert:.1f}/5)")
                break
    return "\n".join(beschreibung)

