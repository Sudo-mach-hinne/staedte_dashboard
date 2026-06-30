"""
Modulname: stil.py
Beschreibung: Zentrales Styling fuer alle Seiten (Hauptseite + Unterseiten).
              Buendelt Weather-Icons-Font, Hintergrundbild und CSS an einer
              Stelle, damit der Style nicht mehr auf jeder Seite dupliziert wird.
Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""

import streamlit as st
import base64
import os

# Name der Hintergrundbild-Datei (liegt im Projekt-Hauptverzeichnis)
HINTERGRUND_DATEI = "Clouds_background.jpg"

# Fallback-Verlauf, falls das Bild nicht gefunden wird
FALLBACK_VERLAUF = (
    "background: linear-gradient(170deg, #a8d8ea 0%, #87ceeb 35%, "
    "#b0d4e8 55%, #f7c59f 78%, #f4a574 92%, #e8856a 100%);"
)


def _hintergrund_css():
    """
    Baut den CSS-Schnipsel fuer den Seitenhintergrund.

    Sucht das Hintergrundbild relativ zum Projekt-Hauptverzeichnis (also dem
    Ordner, in dem stil.py liegt). Dadurch funktioniert der Aufruf sowohl von
    der Hauptseite (app.py) als auch aus dem pages/-Unterordner heraus.

    Rueckgabe:
        str -- CSS fuer 'background', entweder mit eingebettetem Bild
               (Base64) oder dem Fallback-Verlauf.
    """
    # Verzeichnis dieser Datei = Projekt-Hauptverzeichnis
    basis = os.path.dirname(__file__)
    bild_pfad = os.path.join(basis, HINTERGRUND_DATEI)

    if os.path.exists(bild_pfad):
        # Bild als Base64 einbetten, damit Streamlit es nicht blockiert
        with open(bild_pfad, "rb") as f:
            bild_b64 = base64.b64encode(f.read()).decode()
        return (
            f'background-image: url("data:image/jpeg;base64,{bild_b64}"); '
            f"background-size: cover; background-position: center; "
            f"background-attachment: fixed;"
        )

    return FALLBACK_VERLAUF


def lade_css():
    """
    Laedt das komplette Seiten-Styling: Weather-Icons-Font, Hintergrundbild
    und CSS. Auf jeder Seite einmal direkt nach st.set_page_config() aufrufen.

    Beispiel:
        import stil
        st.set_page_config(page_title="...", layout="wide")
        stil.lade_css()
    """
    # Weather-Icons-Font einbinden
    st.markdown(
        '<link rel="stylesheet" '
        'href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/'
        '2.0.10/css/weather-icons.min.css">',
        unsafe_allow_html=True,
    )

    hintergrund = _hintergrund_css()

    # CSS-Block. Doppelte geschweifte Klammern {{ }} sind noetig, weil der
    # f-String sonst die Klammern als Platzhalter interpretieren wuerde.
    # Jede Regel ist per CSS-Kommentar /* ... */ erklaert.
    st.markdown(
        f"""
        <style>
        /* .stApp = der gesamte App-Container: hier kommt der Hintergrund rein
           (entweder das Bild als Base64 oder der Fallback-Verlauf). */
        .stApp {{
            {hintergrund}
        }}
        /* ::before legt eine halbtransparente weisse Schicht UEBER den
           Hintergrund. Dadurch wird das Bild aufgehellt und Text bleibt gut
           lesbar. pointer-events: none, damit die Schicht keine Klicks abfaengt. */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(255, 255, 255, 0.55);
            z-index: 0;
            pointer-events: none;
        }}
        /* Sidebar (linkes Menue) leicht durchscheinend + Weichzeichner
           dahinter -> moderner "Milchglas"-Effekt. */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.4);
            backdrop-filter: blur(10px);
        }}
        /* st.metric-Kacheln (z. B. Hoechst-/Tiefsttemperatur): weisser
           Hintergrund mit abgerundeten Ecken, damit sie sich vom Bild abheben. */
        .stMetric {{
            background: rgba(255, 255, 255, 0.65);
            border-radius: 12px;
            padding: 10px;
        }}
        /* Hauptueberschrift (st.title) -- dunkelblau und gross. */
        h1 {{
            color: #1a3a5c !important;
            font-size: 2.2rem !important;
        }}
        /* Zwischenueberschriften (### / ####) -- gleiche Farbe, kleiner. */
        h2, h3 {{
            color: #1a3a5c !important;
            font-size: 1.6rem !important;
        }}
        /* Normaler Text, Labels und Bildunterschriften -- einheitliche
           Schriftgroesse und dunkle Farbe fuer Lesbarkeit auf dem Bild. */
        p, label, div[data-testid="stCaptionContainer"], .stMarkdown {{
            font-size: 15px !important;
            color: #1a1a2e !important;
        }}
        /* Buttons (z. B. "Suchen") -- heller, halbtransparenter Hintergrund
           mit Rand und abgerundeten Ecken, passend zum Gesamtlook. */
        .stButton > button {{
            background: rgba(255, 255, 255, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.85);
            border-radius: 8px;
            color: #1a3a5c;
            font-size: 15px !important;
        }}
        /* Hover-Zustand: Button wird beim Drueberfahren deutlicher weiss. */
        .stButton > button:hover {{
            background: rgba(255, 255, 255, 0.9);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )