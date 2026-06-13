"""
Modulname: Historisches_Wetter.py
Beschreibung: Streamlit-Unterseite -- Historische Wetterdaten mit Diagrammen
Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import api_client
import base64
import os
from datetime import date, timedelta

# ─────────────────────────────────────────────
# SEITENKONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(page_title="Historisches Wetter", layout="wide")

# ─────────────────────────────────────────────
# WEATHER ICONS FONT
# ─────────────────────────────────────────────
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.10/css/weather-icons.min.css">
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HINTERGRUNDBILD (identisch mit Hauptseite)
# ─────────────────────────────────────────────
hintergrund_css = "background: linear-gradient(170deg, #a8d8ea 0%, #87ceeb 35%, #b0d4e8 55%, #f7c59f 78%, #f4a574 92%, #e8856a 100%);"

bild_pfad = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Clouds_background.jpg")
if os.path.exists(bild_pfad):
    with open(bild_pfad, "rb") as f:
        bild_b64 = base64.b64encode(f.read()).decode()
    hintergrund_css = f'background-image: url("data:image/jpeg;base64,{bild_b64}"); background-size: cover; background-position: center; background-attachment: fixed;'

# ─────────────────────────────────────────────
# CSS-STYLING
# ─────────────────────────────────────────────
st.markdown(f"""
    <style>
    .stApp {{
        {hintergrund_css}
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(255, 255, 255, 0.55);
        z-index: 0;
        pointer-events: none;
    }}
    .stMetric {{
        background: rgba(255, 255, 255, 0.65);
        border-radius: 12px;
        padding: 10px;
    }}
    h1 {{
        color: #1a3a5c !important;
        font-size: 2.2rem !important;
    }}
    h2, h3 {{
        color: #1a3a5c !important;
        font-size: 1.6rem !important;
    }}
    p, label, div[data-testid="stCaptionContainer"], .stMarkdown {{
        font-size: 15px !important;
        color: #1a1a2e !important;
    }}
    .stButton > button {{
        background: rgba(255, 255, 255, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.85);
        border-radius: 8px;
        color: #1a3a5c;
        font-size: 15px !important;
    }}
    .stButton > button:hover {{
        background: rgba(255, 255, 255, 0.9);
    }}
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SEITENTITEL
# ─────────────────────────────────────────────
st.title("📅 Historisches Wetter")
st.markdown("Gib einen Ort ein und wähle einen Zeitraum, um vergangene Wetterdaten als Diagramm zu erkunden.")
st.divider()

# ─────────────────────────────────────────────
# STADTSUCHE
# Freie Texteingabe mit Geocoding
# ─────────────────────────────────────────────
col_input, col_button = st.columns([4, 1])
with col_input:
    stadtname = st.text_input(
        "Ort",
        placeholder="z. B. Berlin, Reykjavik, Buenos Aires ...",
        key="hist_stadtname",
        on_change=lambda: st.session_state.update({"hist_suchen": True})
    )
with col_button:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 Suchen") or st.session_state.get("hist_suchen"):
        st.session_state["hist_suchen"] = False
        if stadtname.strip():
            try:
                with st.spinner(f"Suche nach {stadtname}..."):
                    treffer = api_client.koordinaten_abrufen(stadtname.strip())
                st.session_state["hist_treffer"] = treffer
                st.session_state["hist_gewaehlt"] = None
            except RuntimeError:
                st.error("Ort nicht gefunden. Bitte versuche es mit einem anderen Namen.")

# ─────────────────────────────────────────────
# TREFFERAUSWAHL bei mehreren Ergebnissen
# ─────────────────────────────────────────────
if st.session_state.get("hist_treffer") and not st.session_state.get("hist_gewaehlt"):
    treffer = st.session_state["hist_treffer"]
    if len(treffer) == 1:
        st.session_state["hist_gewaehlt"] = treffer[0]
        st.rerun()
    else:
        st.info("Mehrere Orte gefunden — welchen meinst du?")
        for geo in treffer:
            label = f"{geo['name']} — {geo['region']}, {geo['land']}"
            if st.button(label, key=f"hist_{geo['breitengrad']}_{geo['laengengrad']}"):
                st.session_state["hist_gewaehlt"] = geo
                st.rerun()

# ─────────────────────────────────────────────
# ZEITRAUMAUSWAHL UND DIAGRAMME
# Nur anzeigen wenn ein Ort gewählt wurde
# ─────────────────────────────────────────────
if st.session_state.get("hist_gewaehlt"):
    geo = st.session_state["hist_gewaehlt"]
    ort_info = geo['name']
    if geo.get('kreis'):
        ort_info += f", {geo['kreis']}"
    if geo.get('region'):
        ort_info += f", {geo['region']}"
    if geo.get('land'):
        ort_info += f", {geo['land']}"
    st.markdown(f"**Gewählter Ort:** {ort_info}")
    st.divider()

    heute = date.today()
    gestern = heute - timedelta(days=1)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Von**")
        v1, v2, v3 = st.columns(3)
        with v1:
            von_tag = st.number_input("Tag", min_value=1, max_value=31, value=1, step=1, key="von_tag")
        with v2:
            von_monat = st.number_input("Monat", min_value=1, max_value=12, value=1, step=1, key="von_monat")
        with v3:
            von_jahr = st.number_input("Jahr", min_value=1940, max_value=heute.year, value=heute.year - 1, step=1, key="von_jahr")

    with col2:
        st.markdown("**Bis**")
        b1, b2, b3 = st.columns(3)
        with b1:
            bis_tag = st.number_input("Tag", min_value=1, max_value=31, value=gestern.day, step=1, key="bis_tag")
        with b2:
            bis_monat = st.number_input("Monat", min_value=1, max_value=12, value=gestern.month, step=1, key="bis_monat")
        with b3:
            bis_jahr = st.number_input("Jahr", min_value=1940, max_value=heute.year, value=gestern.year, step=1, key="bis_jahr")

    # ─────────────────────────────────────────
    # DATUM ZUSAMMENSETZEN UND VALIDIEREN
    # ─────────────────────────────────────────
    try:
        datum_von = date(int(von_jahr), int(von_monat), int(von_tag))
        datum_bis = date(int(bis_jahr), int(bis_monat), int(bis_tag))
    except ValueError:
        st.warning("⚠️ Ungültiges Datum — bitte prüfe Tag, Monat und Jahr.")
        st.stop()

    if datum_von < date(1940, 1, 1):
        st.warning("⚠️ Wetteraufzeichnungen sind erst ab dem 1. Januar 1940 verfügbar.")
        st.stop()

    if datum_von >= datum_bis:
        st.warning("⚠️ Das Startdatum muss vor dem Enddatum liegen.")
        st.stop()

    if datum_bis > gestern:
        st.warning("⚠️ Das Enddatum darf nicht in der Zukunft liegen.")
        st.stop()

    # ─────────────────────────────────────────
    # DATEN ABRUFEN
    # ─────────────────────────────────────────
    with st.spinner(f"Lade historische Wetterdaten für {geo['name']}..."):
        try:
            daten = api_client.historisches_wetter_abrufen(
                geo["breitengrad"],
                geo["laengengrad"],
                datum_von.strftime("%Y-%m-%d"),
                datum_bis.strftime("%Y-%m-%d"),
            )
        except RuntimeError as fehler:
            st.error(f"Fehler beim Abrufen der Daten: {fehler}")
            st.stop()

    # ─────────────────────────────────────────
    # DATEN AUFBEREITEN
    # ─────────────────────────────────────────
    df = pd.DataFrame(daten)
    df["datum"] = pd.to_datetime(df["datum"])
    df["temperatur_mittel"] = (df["temperatur_max"] + df["temperatur_min"]) / 2

    # ─────────────────────────────────────────
    # KENNZAHLEN
    # ─────────────────────────────────────────
    st.markdown(f"### 📊 {geo['name']} — {datum_von.strftime('%d.%m.%Y')} bis {datum_bis.strftime('%d.%m.%Y')}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ø Temperatur", f"{df['temperatur_mittel'].mean():.1f} °C")
    with col2:
        st.metric("Höchsttemperatur", f"{df['temperatur_max'].max():.1f} °C")
    with col3:
        st.metric("Tiefsttemperatur", f"{df['temperatur_min'].min():.1f} °C")
    with col4:
        st.metric("Gesamtniederschlag", f"{df['niederschlag'].sum():.1f} mm")

    st.divider()

    # ─────────────────────────────────────────
    # DIAGRAMM 1: TEMPERATURVERLAUF
    # Liniendiagramm mit Min/Max/Mittel als Flaeche
    # ─────────────────────────────────────────
    st.markdown("#### 🌡️ Temperaturverlauf")

    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=df["datum"],
        y=df["temperatur_max"],
        name="Max",
        line=dict(color="#e8856a", width=1.5),
        fill=None,
    ))
    fig_temp.add_trace(go.Scatter(
        x=df["datum"],
        y=df["temperatur_min"],
        name="Min",
        line=dict(color="#87ceeb", width=1.5),
        fill="tonexty",
        fillcolor="rgba(135, 206, 235, 0.2)",
    ))
    fig_temp.add_trace(go.Scatter(
        x=df["datum"],
        y=df["temperatur_mittel"],
        name="Mittel",
        line=dict(color="#1a3a5c", width=2),
    ))
    fig_temp.update_layout(
        plot_bgcolor="rgba(255,255,255,0.7)",
        paper_bgcolor="rgba(255,255,255,0)",
        yaxis_title="Temperatur (°C)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_temp, use_container_width=True)

    st.divider()

    # ─────────────────────────────────────────
    # DIAGRAMM 2: NIEDERSCHLAG
    # Balkendiagramm
    # ─────────────────────────────────────────
    st.markdown("#### 🌧️ Niederschlagsverlauf")

    fig_regen = px.bar(
        df,
        x="datum",
        y="niederschlag",
        labels={"datum": "Datum", "niederschlag": "Niederschlag (mm)"},
        color_discrete_sequence=["#4a90d9"],
    )
    fig_regen.update_layout(
        plot_bgcolor="rgba(255,255,255,0.7)",
        paper_bgcolor="rgba(255,255,255,0)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_regen, use_container_width=True)