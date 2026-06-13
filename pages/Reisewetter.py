"""
Modulname: Reisewetter.py
Beschreibung: Streamlit-Unterseite -- Reisewetter mit Jahresübersicht
Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import api_client
import base64
import os

# ─────────────────────────────────────────────
# SEITENKONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(page_title="Reisewetter", layout="wide")

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
st.title("✈️ Reisewetter")
st.markdown("Gib eine Stadt oder Region ein und erhalte eine Jahresübersicht mit Klimadaten — ideal zur Reiseplanung.")
st.divider()

# ─────────────────────────────────────────────
# STADTSUCHE
# Geocoding über Open-Meteo
# ─────────────────────────────────────────────
col_input, col_button = st.columns([4, 1])
with col_input:
    reiseziel = st.text_input(
        "Reiseziel",
        placeholder="z. B. Lissabon, Tokio, Mallorca ...",
        key="reiseziel_input",
        on_change=lambda: st.session_state.update({"reise_suchen": True})
    )
with col_button:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 Suchen") or st.session_state.get("reise_suchen"):
        st.session_state["reise_suchen"] = False
        if reiseziel.strip():
            try:
                with st.spinner(f"Suche nach {reiseziel}..."):
                    treffer = api_client.koordinaten_abrufen(reiseziel.strip())
                st.session_state["reise_treffer"] = treffer
                st.session_state["reise_gewaehlt"] = None
            except RuntimeError:
                st.error("Stadt nicht gefunden. Bitte versuche es mit einem anderen Namen.")

# ─────────────────────────────────────────────
# TREFFERAUSWAHL bei mehreren Ergebnissen
# ─────────────────────────────────────────────
if st.session_state.get("reise_treffer") and not st.session_state.get("reise_gewaehlt"):
    treffer = st.session_state["reise_treffer"]
    if len(treffer) == 1:
        st.session_state["reise_gewaehlt"] = treffer[0]
        st.rerun()
    else:
        st.info("Mehrere Orte gefunden — welchen meinst du?")
        for geo in treffer:
            label = f"{geo['name']} — {geo['region']}, {geo['land']}"
            if st.button(label, key=f"reise_{geo['breitengrad']}_{geo['laengengrad']}"):
                st.session_state["reise_gewaehlt"] = geo
                st.rerun()

# ─────────────────────────────────────────────
# KLIMADATEN ABRUFEN UND ANZEIGEN
# ─────────────────────────────────────────────
if st.session_state.get("reise_gewaehlt"):
    geo = st.session_state["reise_gewaehlt"]

    st.markdown(f"### 🌍 {geo['name']}, {geo['land']}")
    st.caption("Klimadaten basieren auf dem Durchschnitt der Jahre 1991–2020.")

    with st.spinner("Lade Klimadaten..."):
        try:
            klima = api_client.reisewetter_abrufen(geo["breitengrad"], geo["laengengrad"])
        except RuntimeError as fehler:
            st.error(f"Fehler beim Abrufen der Klimadaten: {fehler}")
            st.stop()

    df = pd.DataFrame(klima)

    # ─────────────────────────────────────────
    # KENNZAHLEN
    # ─────────────────────────────────────────
    bester_monat = df.loc[df["temperatur_max"].idxmax(), "monat"]
    trockenster_monat = df.loc[df["niederschlag"].idxmin(), "monat"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Wärmster Monat", bester_monat)
    with col2:
        st.metric("Trockenster Monat", trockenster_monat)
    with col3:
        st.metric("Ø Jahrestemperatur", f"{df['temperatur_max'].mean():.1f} °C")

    st.divider()

    # ─────────────────────────────────────────
    # DIAGRAMM 1: TEMPERATUR JAHRESÜBERSICHT
    # ─────────────────────────────────────────
    st.markdown("#### 🌡️ Temperatur im Jahresverlauf")

    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=df["monat"],
        y=df["temperatur_max"],
        name="Ø Max",
        line=dict(color="#e8856a", width=2.5),
        fill=None,
    ))
    fig_temp.add_trace(go.Scatter(
        x=df["monat"],
        y=df["temperatur_min"],
        name="Ø Min",
        line=dict(color="#87ceeb", width=2.5),
        fill="tonexty",
        fillcolor="rgba(135, 206, 235, 0.25)",
    ))
    fig_temp.update_layout(
        plot_bgcolor="rgba(255,255,255,0.7)",
        paper_bgcolor="rgba(255,255,255,0)",
        yaxis_title="Temperatur (°C)",
        xaxis_title="Monat",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_temp, use_container_width=True)

    st.divider()

    # ─────────────────────────────────────────
    # DIAGRAMM 2: NIEDERSCHLAG JAHRESÜBERSICHT
    # ─────────────────────────────────────────
    st.markdown("#### 🌧️ Niederschlag im Jahresverlauf")

    fig_regen = px.bar(
        df,
        x="monat",
        y="niederschlag",
        labels={"monat": "Monat", "niederschlag": "Ø Niederschlag (mm)"},
        color_discrete_sequence=["#4a90d9"],
    )
    fig_regen.update_layout(
        plot_bgcolor="rgba(255,255,255,0.7)",
        paper_bgcolor="rgba(255,255,255,0)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_regen, use_container_width=True)