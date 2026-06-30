"""
Modulname: 2_Niederschlagsradar.py
Beschreibung: Streamlit-Unterseite -- Niederschlagsradar (RainViewer).
              Zeigt Radar-Niederschlag als Overlay auf einer Karte. Statt einer
              flackernden Auto-Animation steuert ein Zeitschieberegler, welcher
              Radar-Zeitpunkt angezeigt wird -- das laeuft stabil im Streamlit-Modell.
Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd
import datetime
import api_client
import stil

# ─────────────────────────────────────────────
# SEITENKONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(page_title="Niederschlagsradar", layout="wide")

# ──────────────────────────────
# STYLING (Font, Hintergrund, CSS -- ausgelagert in stil.py)
# ──────────────────────────────
stil.lade_css()

# RainViewer-API: liefert die Zeitpunkte der verfuegbaren Radarbilder
RAINVIEWER_API = "https://api.rainviewer.com/public/weather-maps.json"

# ─────────────────────────────────────────────
# SEITENTITEL
# ─────────────────────────────────────────────
st.title("🌧️ Niederschlagsradar")
st.markdown(
    "Gib einen Ort ein und sieh dir den Niederschlag der letzten zwei Stunden an. "
    "Mit dem Zeitschieberegler bewegst du dich durch die Radarbilder."
)
st.divider()


# ─────────────────────────────────────────────
# RADAR-ZEITPUNKTE ABRUFEN (gecacht)
# Die Frames werden nur EINMAL geholt und 5 Minuten zwischengespeichert.
# Dadurch wird beim Schieben nicht bei jedem Schritt neu geladen.
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def radar_frames_abrufen():
    """
    Holt die verfuegbaren Radar-Zeitpunkte von RainViewer.

    Rueckgabe:
        Tupel (host, frames):
            host (str)   -- Basis-URL fuer die Radar-Kacheln
            frames (list)-- Liste von Dicts, je Zeitpunkt mit 'time' und 'path'
        oder loest RuntimeError bei Fehler aus.
    """
    try:
        antwort = requests.get(RAINVIEWER_API, timeout=10)
        antwort.raise_for_status()
        daten = antwort.json()
        host = daten["host"]
        # past = vergangene Radarbilder (letzte 2 Stunden),
        # nowcast = Vorhersage (naechste ~30 Minuten).
        # Wir markieren jeden Frame mit "prognose" True/False, damit der
        # Schieberegler spaeter Vergangenheit und Zukunft unterscheiden kann.
        vergangen = [
            {**f, "prognose": False} for f in daten["radar"]["past"]
        ]
        zukunft = [
            {**f, "prognose": True} for f in daten["radar"].get("nowcast", [])
        ]
        frames = vergangen + zukunft
        return host, frames
    except Exception as fehler:
        raise RuntimeError(f"Radar-Daten nicht erreichbar: {fehler}")


# ─────────────────────────────────────────────
# STADTSUCHE
# Geocoding über Open-Meteo (gleiches Muster wie auf den anderen Seiten)
# ─────────────────────────────────────────────
col_input, col_button = st.columns([4, 1])
with col_input:
    ort = st.text_input(
        "Ort",
        placeholder="z. B. Leipzig, Halle, Hamburg ...",
        key="radar_input",
        on_change=lambda: st.session_state.update({"radar_suchen": True}),
    )
with col_button:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 Suchen") or st.session_state.get("radar_suchen"):
        st.session_state["radar_suchen"] = False
        if ort.strip():
            try:
                with st.spinner(f"Suche nach {ort}..."):
                    treffer = api_client.koordinaten_abrufen(ort.strip())
                st.session_state["radar_treffer"] = treffer
                st.session_state["radar_gewaehlt"] = None
            except RuntimeError:
                st.error("Ort nicht gefunden. Bitte versuche es mit einem anderen Namen.")

# ─────────────────────────────────────────────
# TREFFERAUSWAHL bei mehreren Ergebnissen
# ─────────────────────────────────────────────
if st.session_state.get("radar_treffer") and not st.session_state.get("radar_gewaehlt"):
    treffer = st.session_state["radar_treffer"]
    if len(treffer) == 1:
        st.session_state["radar_gewaehlt"] = treffer[0]
        st.rerun()
    else:
        st.info("Mehrere Orte gefunden — welchen meinst du?")
        for geo in treffer:
            label = f"{geo['name']} — {geo['region']}, {geo['land']}"
            if st.button(label, key=f"radar_{geo['breitengrad']}_{geo['laengengrad']}"):
                st.session_state["radar_gewaehlt"] = geo
                st.rerun()

# ─────────────────────────────────────────────
# RADARKARTE ANZEIGEN
# ─────────────────────────────────────────────
if st.session_state.get("radar_gewaehlt"):
    geo = st.session_state["radar_gewaehlt"]

    st.markdown(f"### 🌍 {geo['name']}, {geo['land']}")

    # Radar-Frames laden (gecacht)
    try:
        host, frames = radar_frames_abrufen()
    except RuntimeError as fehler:
        st.error(str(fehler))
        st.stop()

    if not frames:
        st.warning("Aktuell sind keine Radardaten verfügbar.")
        st.stop()

    # ─────────────────────────────────────────
    # ZEITSCHIEBEREGLER
    # Jeder Frame hat einen Unix-Zeitstempel. Wir wandeln ihn in eine lesbare
    # Uhrzeit um und lassen den Nutzer den Zeitpunkt waehlen. Standard: der
    # neueste Frame (also der letzte in der Liste).
    # ─────────────────────────────────────────
    # Nur die vergangenen Radarbilder fuer die Karte verwenden (RainViewer-Radar).
    # Die Zukunft kommt weiter unten aus Open-Meteo (zuverlaessige Quelle).
    vergangene_frames = [f for f in frames if not f["prognose"]]
    if not vergangene_frames:
        vergangene_frames = frames  # Sicherheitsnetz, falls alle als prognose markiert

    # ─────────────────────────────────────────
    # VORHERSAGEDATEN HOLEN (Open-Meteo)
    # Wird vor der Karte geladen, damit der Zukunfts-Marker daraus gebaut
    # werden kann. Gleiche Funktion wie auf der Seite "Stuendliches Wetter".
    # ─────────────────────────────────────────
    with st.spinner("Lade Vorhersage..."):
        try:
            stunden = api_client.stuendlich_abrufen(
                geo["breitengrad"], geo["laengengrad"]
            )
        except RuntimeError:
            stunden = []  # Karte soll auch ohne Vorhersage funktionieren

    # Nur die kommenden 24 Stunden ab jetzt herausfiltern.
    jetzt = datetime.datetime.now()
    kommende = []
    for s in stunden:
        zeitpunkt = datetime.datetime.fromisoformat(s["zeit"])
        if jetzt <= zeitpunkt <= jetzt + datetime.timedelta(hours=24):
            kommende.append({
                "zeit": zeitpunkt,
                "niederschlag": s["niederschlag"] or 0.0,
            })

    # ─────────────────────────────────────────
    # MODUSWAHL: Vergangenheit (Radar) oder Zukunft (Vorhersage-Marker)
    # ─────────────────────────────────────────
    modus = st.radio(
        "Was möchtest du sehen?",
        ["🛰️ Vergangenheit (Radar)", "🔮 Zukunft (Vorhersage)"],
        horizontal=True,
    )

    # ─────────────────────────────────────────
    # KARTE BAUEN (Grundkarte fuer beide Modi gleich)
    # zoom_start=7, weil RainViewer-Radar nur bis Zoomstufe 7 Kacheln liefert.
    # ─────────────────────────────────────────
    karte = folium.Map(
        location=[geo["breitengrad"], geo["laengengrad"]],
        zoom_start=7,
        max_zoom=7,
        tiles="CartoDB positron",
    )

    # Ortsname (+ Bundesland) fuer Tooltip/Popup
    if geo.get("region"):
        marker_text = f"{geo['name']}, {geo['region']}"
    else:
        marker_text = geo["name"]

    if modus.startswith("🛰️"):
        # ----- VERGANGENHEIT: RainViewer-Radarflaeche -----
        zeit_labels = [
            datetime.datetime.fromtimestamp(f["time"]).strftime("%H:%M")
            for f in vergangene_frames
        ]
        gewaehltes_label = st.select_slider(
            "Zeitpunkt der Radarmessung",
            options=zeit_labels,
            value=zeit_labels[-1],
        )
        aktiver_frame = vergangene_frames[zeit_labels.index(gewaehltes_label)]

        # {z}/{x}/{y} fuellt folium automatisch; 256 = Kachelgroesse,
        # 2 = Farbschema, 1_1 = geglaettet + mit Schatten.
        tile_url = f"{host}{aktiver_frame['path']}/256/{{z}}/{{x}}/{{y}}/2/1_1.png"
        folium.TileLayer(
            tiles=tile_url,
            attr="RainViewer",
            name="Niederschlag",
            opacity=0.65,
            overlay=True,
            control=False,
        ).add_to(karte)

        folium.Marker(
            [geo["breitengrad"], geo["laengengrad"]],
            tooltip=marker_text,
            popup=marker_text,
        ).add_to(karte)

        karten_caption = (
            f"Vergangene Radarmessung um {gewaehltes_label} Uhr • "
            "Quelle: RainViewer • Blau = leichter, Gelb/Rot = starker Niederschlag"
        )

    else:
        # ----- ZUKUNFT: Vorhersage als farbiger Kreis-Marker -----
        if not kommende:
            st.info("Keine Vorhersagedaten für die nächsten 24 Stunden verfügbar.")
            karten_caption = ""
        else:
            # Zeitregler ueber die kommenden Stunden
            stunden_labels = [k["zeit"].strftime("%a %H:%M") for k in kommende]
            gewaehltes_label = st.select_slider(
                "Vorhersage-Zeitpunkt",
                options=stunden_labels,
                value=stunden_labels[0],
            )
            aktive_stunde = kommende[stunden_labels.index(gewaehltes_label)]
            mm = aktive_stunde["niederschlag"]

            # ─────────────────────────────────────
            # KREIS-DARSTELLUNG nach Regenmenge
            # Farbe: fliessend von hellblau (wenig) zu tiefem Dunkelblau (viel).
            # Groesse: waechst mit der Menge.
            # Kein Regen: winziger, fast unsichtbarer Punkt.
            # ─────────────────────────────────────
            def _kreis_eigenschaften(menge):
                """
                Liefert (radius, farbe, deckkraft) fuer eine Regenmenge in mm.
                Farbe wird zwischen Hellblau und Tiefblau interpoliert.
                """
                # Kein nennenswerter Regen -> winzig und fast transparent
                if menge < 0.1:
                    return 4, "#cfe3f5", 0.25

                # "anteil" geht von 0.0 (wenig) bis 1.0 (sehr viel, ab 10 mm).
                # min(...) deckelt sehr starke Werte, damit der Kreis nicht
                # ueber die Karte hinauswaechst.
                anteil = min(menge / 10.0, 1.0)

                # Radius waechst von ca. 8 (leicht) bis 38 (sehr stark) Pixel.
                radius = 8 + anteil * 30

                # Farbe interpolieren: hellblau (173,214,244) -> tiefblau (4,44,83).
                hell = (173, 214, 244)
                tief = (4, 44, 83)
                r = round(hell[0] + (tief[0] - hell[0]) * anteil)
                g = round(hell[1] + (tief[1] - hell[1]) * anteil)
                b = round(hell[2] + (tief[2] - hell[2]) * anteil)
                farbe = f"#{r:02x}{g:02x}{b:02x}"

                return radius, farbe, 1.0  # voll ausgefuellt (Deckkraft 1.0)

            def _stufe_text(menge):
                if menge < 0.1:
                    return "trocken"
                if menge < 1:
                    return "leichter Regen"
                if menge < 3:
                    return "mäßiger Regen"
                if menge < 5:
                    return "starker Regen"
                return "sehr starker Regen"

            radius, farbe, deckkraft = _kreis_eigenschaften(mm)

            folium.CircleMarker(
                location=[geo["breitengrad"], geo["laengengrad"]],
                radius=radius,
                color=farbe,
                weight=1,
                fill=True,
                fill_color=farbe,
                fill_opacity=deckkraft,
                opacity=deckkraft,
                tooltip=f"{marker_text}: {mm:.1f} mm ({_stufe_text(mm)})",
                popup=f"{marker_text}: {mm:.1f} mm ({_stufe_text(mm)})",
            ).add_to(karte)

            # Zusaetzlich der normale Pin, damit der Ort klar markiert bleibt
            folium.Marker(
                [geo["breitengrad"], geo["laengengrad"]],
                tooltip=marker_text,
            ).add_to(karte)

            karten_caption = (
                f"Vorhersage für {gewaehltes_label} Uhr: **{mm:.1f} mm** "
                f"({_stufe_text(mm)}) • Quelle: Open-Meteo"
            )

    # ─────────────────────────────────────────
    # KARTE ANZEIGEN (einmal, fuer beide Modi)
    # Fester key gegen Flackern: streamlit-folium erkennt dieselbe Karte.
    # ─────────────────────────────────────────
    st_folium(
        karte,
        width=None,
        height=500,
        key="radar_karte",
        returned_objects=[],
    )

    if karten_caption:
        st.caption(karten_caption)

    # ─────────────────────────────────────────────
    # VORHERSAGE-ÜBERSICHT (Diagramm)
    # Ergaenzend zur Karte: das Balkendiagramm zeigt alle 24 Stunden auf einen
    # Blick. Nutzt dieselben Daten ("kommende"), die oben schon geladen wurden.
    # ─────────────────────────────────────────────
    st.divider()
    st.markdown("### 📊 Niederschlagsvorhersage im Überblick (nächste 24 Stunden)")

    if not kommende:
        st.info("Keine Vorhersagedaten für die nächsten 24 Stunden verfügbar.")
    else:
        df_vorhersage = pd.DataFrame({
            "Uhrzeit": [k["zeit"].strftime("%a %H:%M") for k in kommende],
            "Niederschlag (mm)": [k["niederschlag"] for k in kommende],
        })

        # Kennzahl: Gesamtniederschlag der naechsten 24 Stunden
        gesamt = df_vorhersage["Niederschlag (mm)"].sum()
        if gesamt < 0.1:
            st.success("🌤️ In den nächsten 24 Stunden wird kein Regen erwartet.")
        else:
            st.metric("Erwarteter Niederschlag (24 h)", f"{gesamt:.1f} mm")

        # Balkendiagramm der stuendlichen Niederschlagsvorhersage
        fig = px.bar(
            df_vorhersage,
            x="Uhrzeit",
            y="Niederschlag (mm)",
            color_discrete_sequence=["#4a90d9"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(255,255,255,0.7)",
            paper_bgcolor="rgba(255,255,255,0)",
            hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Vorhersagedaten: Open-Meteo")