"""
Modulname: Stuendliches_Wetter.py
Beschreibung: Streamlit-Unterseite -- Stündliches Wetter (kombiniertes Diagramm)
Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import api_client
import stil

# ─────────────────────────────────────────────
# SEITENKONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(page_title="Stündliches Wetter", layout="wide")

# ──────────────────────────────
# STYLING (Font, Hintergrund, CSS -- ausgelagert in stil.py)
# ──────────────────────────────
stil.lade_css()

# ─────────────────────────────────────────────
# SEITENTITEL
# ─────────────────────────────────────────────
st.title("🕐 Stündliches Wetter")
st.markdown("Gib eine Stadt ein und erhalte die stündliche Vorhersage für die nächsten Tage.")
st.divider()

# ─────────────────────────────────────────────
# STADTSUCHE
# Geocoding über Open-Meteo
# ─────────────────────────────────────────────
col_input, col_button = st.columns([4, 1])
with col_input:
    ort = st.text_input(
        "Ort",
        placeholder="z. B. Leipzig, Hamburg, Wien ...",
        key="stuendlich_input",
        on_change=lambda: st.session_state.update({"stuendlich_suchen": True})
    )
with col_button:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 Suchen") or st.session_state.get("stuendlich_suchen"):
        st.session_state["stuendlich_suchen"] = False
        if ort.strip():
            try:
                with st.spinner(f"Suche nach {ort}..."):
                    treffer = api_client.koordinaten_abrufen(ort.strip())
                st.session_state["stuendlich_treffer"] = treffer
                st.session_state["stuendlich_gewaehlt"] = None
            except RuntimeError:
                st.error("Stadt nicht gefunden. Bitte versuche es mit einem anderen Namen.")

# ─────────────────────────────────────────────
# TREFFERAUSWAHL bei mehreren Ergebnissen
# ─────────────────────────────────────────────
if st.session_state.get("stuendlich_treffer") and not st.session_state.get("stuendlich_gewaehlt"):
    treffer = st.session_state["stuendlich_treffer"]
    if len(treffer) == 1:
        st.session_state["stuendlich_gewaehlt"] = treffer[0]
        st.rerun()
    else:
        st.info("Mehrere Orte gefunden — welchen meinst du?")
        for geo in treffer:
            label = f"{geo['name']} — {geo['region']}, {geo['land']}"
            if st.button(label, key=f"stuendlich_{geo['breitengrad']}_{geo['laengengrad']}"):
                st.session_state["stuendlich_gewaehlt"] = geo
                st.rerun()

# ─────────────────────────────────────────────
# STÜNDLICHE DATEN ABRUFEN UND ANZEIGEN
# ─────────────────────────────────────────────
if st.session_state.get("stuendlich_gewaehlt"):
    geo = st.session_state["stuendlich_gewaehlt"]

    st.markdown(f"### 🌍 {geo['name']}, {geo['land']}")

    with st.spinner("Lade stündliche Wetterdaten..."):
        try:
            stunden = api_client.stuendlich_abrufen(geo["breitengrad"], geo["laengengrad"])
        except RuntimeError as fehler:
            st.error(f"Fehler beim Abrufen der Wetterdaten: {fehler}")
            st.stop()

    df = pd.DataFrame(stunden)
    df["zeit"] = pd.to_datetime(df["zeit"])

    # ─────────────────────────────────────────
    # KENNZAHLEN
    # ─────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Höchsttemperatur", f"{df['temperatur'].max():.1f} °C")
    with col2:
        st.metric("Tiefsttemperatur", f"{df['temperatur'].min():.1f} °C")
    with col3:
        st.metric("Niederschlag gesamt", f"{df['niederschlag'].sum():.1f} mm")

    st.divider()

    # ─────────────────────────────────────────
    # KOMBINIERTES DIAGRAMM
    # Temperatur (Linie, linke Achse) + Niederschlag (Balken, rechte Achse)
    # ─────────────────────────────────────────
    st.markdown("#### 🌡️🌧️ Temperatur und Niederschlag im Verlauf")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Niederschlag als Balken (rechte Achse) -- zuerst, damit Linie darüber liegt
    fig.add_trace(
        go.Bar(
            x=df["zeit"],
            y=df["niederschlag"],
            name="Niederschlag",
            marker_color="rgba(74, 144, 217, 0.6)",
        ),
        secondary_y=True,
    )

    # Temperatur als Linie (linke Achse)
    fig.add_trace(
        go.Scatter(
            x=df["zeit"],
            y=df["temperatur"],
            name="Temperatur",
            line=dict(color="#e8856a", width=2.5),
        ),
        secondary_y=False,
    )

    fig.update_layout(
        plot_bgcolor="rgba(255,255,255,0.7)",
        paper_bgcolor="rgba(255,255,255,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(l=0, r=0, t=10, b=0),
    )
    fig.update_yaxes(title_text="Temperatur (°C)", secondary_y=False)
    fig.update_yaxes(title_text="Niederschlag (mm)", secondary_y=True, rangemode="tozero")
    fig.update_xaxes(title_text="Zeit")

    st.plotly_chart(fig, use_container_width=True)