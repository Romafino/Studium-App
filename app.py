import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Studiengangs-Matching", page_icon="🎓", layout="wide")

@st.cache_data
def lade_fragen():
    return pd.read_csv("fragebogen_kurzversion.csv", sep=";")

@st.cache_data
def lade_studiengaenge():
    df = pd.read_csv("Zuordnung_Studium_Beruf_Vollständig_MOTIVIERT.csv", sep=";")
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

def berechne_match(profil, zeile):
    dims = profil.keys()
    abweichung = np.mean([abs(profil[d] - 3) for d in dims])
    score = max(0, 100 - abweichung * 20)

    if st.session_state.zusatz['motivation'] == "Berufsaussichten" and str(zeile.get("Arbeitsmarktbedarf", "")).lower() == "sehr hoch":
        score *= 1.1

    return min(score, 100)

def beschreibe_profil(profil):
    beschreibung = []

    r_map = {
        "Realistic": "Du hast eine praktische Veranlagung und arbeitest gerne mit Werkzeugen, Maschinen oder in technischen Umgebungen.",
        "Investigative": "Du bist analytisch und forschungsorientiert – du löst gerne komplexe Probleme.",
        "Artistic": "Du bist kreativ, fantasievoll und drückst dich gerne gestalterisch aus.",
        "Social": "Du arbeitest gerne mit Menschen zusammen und hilfst anderen.",
        "Enterprising": "Du bist durchsetzungsfähig, führungsstark und gerne unternehmerisch aktiv.",
        "Conventional": "Du bist organisiert, zuverlässig und arbeitest gerne mit klaren Strukturen."
    }

    b_map = {
        "Openness": "Du bist offen für neue Erfahrungen, neugierig und kreativ.",
        "Conscientiousness": "Du bist verantwortungsbewusst, strukturiert und zielstrebig.",
        "Extraversion": "Du bist kontaktfreudig, aktiv und gerne unter Menschen.",
        "Agreeableness": "Du bist mitfühlend, kooperativ und teamorientiert.",
        "Neuroticism": "Du bist emotional sensibel und reflektiert – du nimmst Dinge oft tiefer wahr."
    }

    beschreibung.append("🔍 **RIASEC-Profil**")
    for dim in ["Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"]:
        if dim in profil:
            score = profil[dim]
            text = r_map.get(dim, "")
            beschreibung.append(f"**{dim}** ({score:.1f}/5): {text}")

    beschreibung.append("\n🧠 **Big Five**")
    for dim in ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]:
        if dim in profil:
            score = profil[dim]
            text = b_map.get(dim, "")
            beschreibung.append(f"**{dim}** ({score:.1f}/5): {text}")

    return "\n".join(beschreibung)

def ergebnisse_seite():
    st.header("📊 Deine Studiengangs-Empfehlungen")

    profil = berechne_profil()
    df = lade_studiengaenge()
    df['Match'] = df.apply(lambda row: berechne_match(profil, row), axis=1)
    df = df.sort_values('Match', ascending=False)

    st.subheader("🧠 Dein Persönlichkeitsprofil")
    st.markdown(beschreibe_profil(profil))

    st.subheader("🎯 Top Studiengänge")
    seite = st.session_state.ergebnis_seite
    pro_seite = 10
    top = df.iloc[seite * pro_seite : (seite + 1) * pro_seite]

    for _, row in top.iterrows():
        studiengang = row.get('Studiengang', 'Unbekannt')
        match = row.get('Match', 0)
        with st.expander(f"{studiengang} — Match: {match:.0f}%"):
            st.write(f"**📌 NC:** {row.get('NC', 'k.A.')}")

            berufe = [row.get(f'Beruf_{i}', '') for i in range(1, 6)]
            berufe = [b for b in berufe if pd.notna(b) and b.strip()]
            st.write(f"**🧑‍🔧 Typische Berufe:** {', '.join(berufe) if berufe else 'k.A.'}")

            st.write(f"**💼 Berufsfelder:** {row.get('Berufsfelder TOP3', 'k.A.')}")
            st.write(f"**🪙 Einstiegsspanne:** {row.get('Einstieg spanne', 'k.A.')}")
            st.write(f"**💰 Einstiegsgehalt:** {row.get('Einstiegsgehalt', 'k.A.')} €")
            st.write(f"**📊 Gehalt nach 5 Jahren:** {row.get('Gehalt nach 5 Jahren', 'k.A.')} €")
            st.write(f"**📈 Arbeitsmarktbedarf:** {row.get('Arbeitsmarktbedarf', 'k.A.')}")

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
