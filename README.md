# Studienmatch App 🎓

Ein interaktives Tool zur Studienberatung basierend auf dem RIASEC-Modell und den Big Five.

## Features

- 40 Fragen (Likert-Skala)
- Persönlichkeitsprofil mit 11 Dimensionen (RIASEC + Big Five)
- Zusatzfragen zu Motivation & Arbeitsumgebung
- Matching mit über 30 Studiengängen (inkl. NC, Berufsfelder, Gehalt, Beschreibung)
- Web-Oberfläche mit Streamlit

## Nutzung

```bash
pip install -r requirements.txt
streamlit run app_neu.py
```

## Dateien

- `app_neu.py`: Die Hauptanwendung
- `fragebogen_kurzversion.csv`: Fragenkatalog
- `Zuordnung_Studium_Beruf_Vollständig_MOTIVIERT.csv`: Studiengangs-Datenbank
