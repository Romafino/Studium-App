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
    def skalierte_beschreibung(name, wert, stufen):
        for (min_val, max_val, text) in stufen:
            if min_val <= wert <= max_val:
                return f"**{name}** ({wert:.1f}/5): {text}"
        return f"**{name}** ({wert:.1f}/5): Beschreibung nicht verfügbar."

    beschreibung = []
    beschreibung.append("🔍 **RIASEC-Profil**")

    riaisec_stufen = {
        "Realistic": [
            (1.0, 2.4, "Du bevorzugst geistige oder kreative Arbeit mehr als praktisches Tun."),
            (2.5, 3.4, "Du fühlst dich in technischen und praktischen Aufgaben phasenweise wohl."),
            (3.5, 5.0, "Du bist handlungsorientiert, praktisch veranlagt und liebst Technik, Werkzeuge oder Maschinen.")
        ],
        "Investigative": [
            (1.0, 2.4, "Analytisches oder forschendes Arbeiten liegt dir weniger."),
            (2.5, 3.4, "Du denkst gerne nach und analysierst – aber nur, wenn es Sinn ergibt."),
            (3.5, 5.0, "Du hast eine starke Neigung zu Forschung, Analyse und tiefem Verständnis.")
        ],
        "Artistic": [
            (1.0, 2.4, "Kreativität spielt in deinem Alltag eher eine untergeordnete Rolle."),
            (2.5, 3.4, "Du hast ein gewisses Gespür für Gestaltung und Ideen, nutzt es aber selektiv."),
            (3.5, 5.0, "Du bist ideenreich, fantasievoll und suchst kreative Ausdrucksformen.")
        ],
        "Social": [
            (1.0, 2.4, "Du arbeitest lieber unabhängig und brauchst nicht ständig den Austausch mit anderen."),
            (2.5, 3.4, "Du schätzt Zusammenarbeit in bestimmten Situationen, bist aber auch gerne für dich."),
            (3.5, 5.0, "Du blühst in sozialen Kontexten auf und hilfst gerne anderen.")
        ],
        "Enterprising": [
            (1.0, 2.4, "Führen, Überzeugen oder Risiko liegen dir eher nicht."),
            (2.5, 3.4, "Du bist manchmal gerne durchsetzungsstark, aber ohne Dominanz."),
            (3.5, 5.0, "Du bist führungsstark, überzeugend und hast ein Gespür für unternehmerisches Handeln.")
        ],
        "Conventional": [
            (1.0, 2.4, "Du fühlst dich mit zu viel Struktur oder Routine schnell eingeschränkt."),
            (2.5, 3.4, "Du schätzt Ordnung, aber brauchst auch Freiraum."),
            (3.5, 5.0, "Du arbeitest gerne organisiert, planvoll und liebst klare Abläufe.")
        ]
    }

    for dim in riaisec_stufen:
        if dim in profil:
            beschreibung.append(skalierte_beschreibung(dim, profil[dim], riaisec_stufen[dim]))

    beschreibung.append("\n🧠 **Big Five Persönlichkeitsprofil**")

    bigfive_stufen = {
        "Openness": [
            (1.0, 2.4, "Du bevorzugst Altbewährtes und hast weniger Interesse an Neuem oder Abstraktem."),
            (2.5, 3.4, "Du bist offen für Neues, wenn es praktikabel und sinnvoll erscheint."),
            (3.5, 5.0, "Du bist neugierig, kreativ und liebst es, neue Perspektiven zu entdecken.")
        ],
        "Conscientiousness": [
            (1.0, 2.4, "Du lässt dich gerne treiben und brauchst Flexibilität."),
            (2.5, 3.4, "Du bist zuverlässig, aber nimmst Regeln nicht zu ernst."),
            (3.5, 5.0, "Du bist verantwortungsvoll, strukturiert und arbeitest zielgerichtet.")
        ],
        "Extraversion": [
            (1.0, 2.4, "Du genießt Ruhe, denkst gerne nach und brauchst Zeit für dich."),
            (2.5, 3.4, "Du bist sozial ausgewogen – du kannst sowohl mit Menschen als auch allein gut umgehen."),
            (3.5, 5.0, "Du bist kommunikativ, energiegeladen und suchst den Austausch.")
        ],
        "Agreeableness": [
            (1.0, 2.4, "Du hinterfragst gerne und sagst klar deine Meinung."),
            (2.5, 3.4, "Du bist hilfsbereit, aber setzt auch klare Grenzen."),
            (3.5, 5.0, "Du bist warmherzig, kooperativ und schätzt harmonische Beziehungen.")
        ],
        "Neuroticism": [
            (1.0, 2.4, "Du bist emotional sehr stabil und lässt dich selten aus der Ruhe bringen."),
            (2.5, 3.4, "Du bist reflektiert und reagierst situationsangemessen."),
            (3.5, 5.0, "Du bist feinfühlig, sensibel und nimmst emotionale Reize stärker wahr.")
        ]
    }

    for dim in bigfive_stufen:
        if dim in profil:
            beschreibung.append(skalierte_beschreibung(dim, profil[dim], bigfive_stufen[dim]))

    return "\n".join(beschreibung)

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
