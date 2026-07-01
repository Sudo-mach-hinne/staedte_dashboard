"""
Modulname: stil.py
Beschreibung: Zentrales Styling fuer alle Seiten (Hauptseite + Unterseiten).
              Buendelt Weather-Icons-Font, Hintergrundbild und CSS an einer
              Stelle, damit der Style nicht mehr auf jeder Seite dupliziert wird.
              Unterstuetzt einen Hell- und einen Dunkel-Modus mit je eigenem
              Himmel-Hintergrund.
Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""

import streamlit as st
import base64
import os

# Hintergrundbilder (liegen im Projekt-Hauptverzeichnis)
HINTERGRUND_HELL = "Clouds_background.jpg"   # heller Wolkenhimmel
HINTERGRUND_DUNKEL = "Clouds_dark.jpg"       # dunkler Regenwolken-Himmel

# Fallback-Verlaeufe, falls das jeweilige Bild nicht gefunden wird
FALLBACK_HELL = (
    "background: linear-gradient(170deg, #a8d8ea 0%, #87ceeb 35%, "
    "#b0d4e8 55%, #f7c59f 78%, #f4a574 92%, #e8856a 100%);"
)
FALLBACK_DUNKEL = (
    "background: linear-gradient(170deg, #1a2233 0%, #232f42 45%, "
    "#2b3a52 70%, #34465f 100%);"
)


def _bild_als_css(dateiname, fallback):
    """
    Baut den CSS-Schnipsel für einen Bildhintergrund.

    Sucht das Bild relativ zum Projekt-Hauptverzeichnis (dem Ordner, in dem
    stil.py liegt). So funktioniert es von der Hauptseite und aus pages/.

    Parameter:
        dateiname (str): Name der Bilddatei
        fallback (str): CSS-Verlauf, falls das Bild fehlt

    Rückgabe:
        str: CSS für 'background' (Bild als Base64), oder der Fallback-Verlauf
            falls die Datei nicht gefunden wird
    """
    basis = os.path.dirname(__file__)
    bild_pfad = os.path.join(basis, dateiname)

    if os.path.exists(bild_pfad):
        with open(bild_pfad, "rb") as f:
            bild_b64 = base64.b64encode(f.read()).decode()
        return (
            f'background-image: url("data:image/jpeg;base64,{bild_b64}"); '
            f"background-size: cover; background-position: center; "
            f"background-attachment: fixed;"
        )

    return fallback


def _modus_waehler():
    """
    Zeigt oben in der Sidebar einen Hell/Dunkel-Umschalter und merkt sich die
    Wahl in st.session_state, damit sie über alle Seiten hinweg gilt.

    Rückgabe:
        str: "Hell" oder "Dunkel"
    """
    # Startwert beim ersten Laden: Hell
    if "design_modus" not in st.session_state:
        st.session_state["design_modus"] = "Hell"

    with st.sidebar:
        modus = st.radio(
            "Design",
            ["☀️ Hell", "🌙 Dunkel"],
            index=0 if st.session_state["design_modus"] == "Hell" else 1,
            horizontal=True,
            key="design_modus_auswahl",
        )

    # Auswahl (mit Emoji) auf "Hell"/"Dunkel" zurueckfuehren und merken
    st.session_state["design_modus"] = "Dunkel" if "Dunkel" in modus else "Hell"
    return st.session_state["design_modus"]


def lade_css():
    """
    Laedt das komplette Seiten-Styling: Weather-Icons-Font, Hintergrundbild
    und CSS -- passend zum gewaehlten Hell- oder Dunkel-Modus.
    Auf jeder Seite einmal direkt nach st.set_page_config() aufrufen.

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

    # Modus-Umschalter anzeigen und Wahl holen
    modus = _modus_waehler()

    # Je nach Modus: Hintergrund, Overlay-Farbe und Textfarben festlegen.
    if modus == "Dunkel":
        hintergrund = _bild_als_css(HINTERGRUND_DUNKEL, FALLBACK_DUNKEL)
        overlay = "rgba(15, 22, 35, 0.55)"      # dunkle Schicht ueber dem Bild
        sidebar_bg = "rgba(20, 28, 42, 0.55)"
        kachel_bg = "rgba(40, 52, 70, 0.70)"
        ueberschrift_farbe = "#dce6f5"          # helles Blau-Weiss
        text_farbe = "#e8edf5"                  # heller Text
        button_bg = "rgba(40, 52, 70, 0.70)"
        button_border = "rgba(120, 140, 170, 0.55)"
        button_text = "#dce6f5"
        button_hover = "rgba(60, 76, 100, 0.85)"
    else:
        hintergrund = _bild_als_css(HINTERGRUND_HELL, FALLBACK_HELL)
        overlay = "rgba(255, 255, 255, 0.55)"   # helle Schicht ueber dem Bild
        sidebar_bg = "rgba(255, 255, 255, 0.4)"
        kachel_bg = "rgba(255, 255, 255, 0.65)"
        ueberschrift_farbe = "#1a3a5c"          # dunkelblau
        text_farbe = "#1a1a2e"                  # dunkler Text
        button_bg = "rgba(255, 255, 255, 0.65)"
        button_border = "rgba(255, 255, 255, 0.85)"
        button_text = "#1a3a5c"
        button_hover = "rgba(255, 255, 255, 0.9)"

    # CSS-Block. Doppelte geschweifte Klammern {{ }} sind noetig, weil der
    # f-String sonst die Klammern als Platzhalter interpretieren wuerde.
    st.markdown(
        f"""
        <style>
        /* .stApp = der gesamte App-Container: hier kommt der Hintergrund rein
           (entweder das Bild als Base64 oder der Fallback-Verlauf). */
        .stApp {{
            {hintergrund}
        }}
        /* ::before legt eine halbtransparente Schicht UEBER den Hintergrund.
           Hell: weiss zum Aufhellen. Dunkel: dunkelblau zum Abdunkeln.
           So bleibt der Text in beiden Modi gut lesbar. */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: {overlay};
            z-index: 0;
            pointer-events: none;
        }}
        /* Sidebar (linkes Menue) leicht durchscheinend + Weichzeichner. */
        section[data-testid="stSidebar"] {{
            background: {sidebar_bg};
            backdrop-filter: blur(10px);
        }}
        /* st.metric-Kacheln: leicht abgesetzter Hintergrund mit runden Ecken. */
        .stMetric {{
            background: {kachel_bg};
            border-radius: 12px;
            padding: 10px;
        }}
        /* Hauptueberschrift (st.title). */
        h1 {{
            color: {ueberschrift_farbe} !important;
            font-size: 2.2rem !important;
        }}
        /* Zwischenueberschriften. */
        h2, h3 {{
            color: {ueberschrift_farbe} !important;
            font-size: 1.6rem !important;
        }}
        /* Normaler Text, Labels und Bildunterschriften. */
        p, label, div[data-testid="stCaptionContainer"], .stMarkdown {{
            font-size: 15px !important;
            color: {text_farbe} !important;
        }}
        /* Buttons. */
        .stButton > button {{
            background: {button_bg};
            border: 1px solid {button_border};
            border-radius: 8px;
            color: {button_text};
            font-size: 15px !important;
        }}
        /* Hover-Zustand. */
        .stButton > button:hover {{
            background: {button_hover};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )