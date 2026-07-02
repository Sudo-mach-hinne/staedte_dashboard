"""
Modulname: 2_Niederschlagsradar.py
Beschreibung: Streamlit-Unterseite -- Niederschlagsradar (RainViewer).
Zeigt den Niederschlag der letzten zwei Stunden als animiertes Radar-Overlay
auf einer Karte. Die Animation laeuft direkt im Browser (JavaScript), nicht
ueber Streamlit-Reruns -- dadurch flackert nichts. Zusaetzlich gibt es eine
Zukunfts-Ansicht mit stuendlicher Vorhersage aus Open-Meteo.

Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""

import streamlit as st
import requests
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import plotly.express as px
import pandas as pd
import datetime
import json
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
    "Gib einen Ort ein und sieh dir den Niederschlag der letzten zwei Stunden "
    "als Animation an. Über den Modus kannst du zwischen der Vergangenheit "
    "(animiertes Radar) und der Zukunft (Vorhersage) umschalten."
)
st.divider()


# ─────────────────────────────────────────────
# RADAR-ZEITPUNKTE ABRUFEN (gecacht)
# Die Frames werden nur EINMAL geholt und 5 Minuten zwischengespeichert.
# Dadurch wird beim Schieben nicht bei jedem Schritt neu geladen.
# ─────────────────────────────────────────────
@st.cache_data(ttl=1800)
def gitter_daten_abrufen(breitengrad, laengengrad):
    """
    Gecachte Huelle um api_client.gitter_niederschlag_abrufen(). 30 Minuten
    Cache, weil sich stuendliche Vorhersagedaten nicht schneller aendern.

    Rückgabe:
        dict: siehe api_client.gitter_niederschlag_abrufen()
    """
    return api_client.gitter_niederschlag_abrufen(breitengrad, laengengrad)


@st.cache_data(ttl=300)
def radar_frames_abrufen():
    """
    Holt die verfügbaren Radar-Zeitpunkte von RainViewer.

    Rückgabe:
        tuple: (host, frames)
            host (str): Basis-URL für die Radar-Kacheln
            frames (list): Liste von Dicts, je ein Zeitpunkt mit 'time',
                'path' und 'prognose' (bool)

    Fehler:
        RuntimeError: Wenn die RainViewer-API nicht erreichbar ist
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
# ANIMIERTE RADAR-KARTE (laeuft im Browser, kein Flackern)
# Baut eine eigenstaendige Leaflet-Karte, die die Radarbilder der letzten
# zwei Stunden per JavaScript nacheinander abspielt. Weil die Animation
# komplett im Browser laeuft (setInterval) und NICHT ueber Streamlit-Reruns,
# gibt es kein Flackern -- das war frueher das Problem bei der Auto-Animation.
# ─────────────────────────────────────────────
def baue_animiertes_radar(host, frames, lat, lon, ortsname):
    """
    Erzeugt den HTML-/JavaScript-Code für eine animierte Radar-Karte.

    Parameter:
        host (str): Basis-URL der RainViewer-Kacheln
        frames (list): Vergangene Radar-Frames (je mit 'time' und 'path')
        lat (float): Breitengrad des Kartenmittelpunkts
        lon (float): Längengrad des Kartenmittelpunkts
        ortsname (str): Beschriftung des Ortsmarkers

    Rückgabe:
        str: Fertiges HTML zum Einbetten mit components.html()
    """
    # Nur die benoetigten Felder als JSON an das JavaScript uebergeben.
    frames_js = json.dumps([{"time": f["time"], "path": f["path"]} for f in frames])

    template = """
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <div style="font-family: sans-serif;">
      <div style="margin-bottom:6px;">
        <button id="radar-toggle"
          style="padding:5px 14px; cursor:pointer; border-radius:6px;
                 border:1px solid #888; background:#ffffff; font-size:14px;">
          &#9208;&#65039; Pause
        </button>
        <span style="margin-left:12px; font-size:14px;">
          Zeitpunkt: <b id="radar-time">--:--</b>
        </span>
      </div>
      <div id="radar-map" style="height:500px; border-radius:8px;"></div>
    </div>
    <script>
      (function() {
        var map = L.map('radar-map', {maxZoom: 7, minZoom: 3}).setView([__LAT__, __LON__], 7);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
          {attribution: '&copy; OpenStreetMap, &copy; CARTO'}).addTo(map);
        L.marker([__LAT__, __LON__]).addTo(map).bindTooltip(__NAME__);

        var host = __HOST__;
        var frames = __FRAMES__;

        // Fuer jeden Zeitpunkt eine Kachel-Ebene vorbereiten.
        var layers = frames.map(function(f) {
          return L.tileLayer(host + f.path + '/256/{z}/{x}/{y}/2/1_1.png', {opacity: 0.65});
        });

        var idx = 0, current = null, playing = true;
        var timeEl = document.getElementById('radar-time');

        function show(i) {
          if (current) { map.removeLayer(current); }
          current = layers[i];
          current.addTo(map);
          var d = new Date(frames[i].time * 1000);
          timeEl.textContent = d.toLocaleTimeString('de-DE',
            {hour: '2-digit', minute: '2-digit'});
        }

        if (layers.length > 0) { show(0); }

        // Alle 0,6 Sekunden zum naechsten Bild springen (Endlosschleife).
        setInterval(function() {
          if (!playing || layers.length === 0) { return; }
          idx = (idx + 1) % layers.length;
          show(idx);
        }, 600);

        // Play/Pause-Schalter
        document.getElementById('radar-toggle').onclick = function() {
          playing = !playing;
          this.innerHTML = playing ? '&#9208;&#65039; Pause' : '&#9654;&#65039; Play';
        };
      })();
    </script>
    """

    return (
        template
        .replace("__LAT__", str(lat))
        .replace("__LON__", str(lon))
        .replace("__HOST__", json.dumps(host))
        .replace("__FRAMES__", frames_js)
        .replace("__NAME__", json.dumps(ortsname))
    )


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
                st.error("😢 Oh no! Diese Stadt ist unbekannt. Vielleicht ein Tippfehler?")

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
        ["🕰️ Vergangenheit (Radar)", "🔮 Zukunft (Vorhersage)"],
        horizontal=True,
    )

    # Ortsname (+ Bundesland) fuer Tooltip/Popup
    if geo.get("region"):
        marker_text = f"{geo['name']}, {geo['region']}"
    else:
        marker_text = geo["name"]

    if "Vergangenheit" in modus:
        # ───── VERGANGENHEIT: animiertes RainViewer-Radar ─────
        # Die Radarbilder der letzten zwei Stunden werden im Browser als
        # Animation abgespielt (kein Streamlit-Rerun -> kein Flackern).
        radar_html = baue_animiertes_radar(
            host,
            vergangene_frames,
            geo["breitengrad"],
            geo["laengengrad"],
            marker_text,
        )
        components.html(radar_html, height=580)
        st.caption(
            "Animiertes Radar der letzten zwei Stunden • Quelle: RainViewer • "
            "Blau = leichter, Gelb/Rot = starker Niederschlag"
        )

    else:
        # ───── ZUKUNFT: Vorhersage als farbiger Kreis-Marker (folium) ─────
        # zoom_start=7, weil RainViewer-Radar nur bis Zoomstufe 7 Kacheln liefert.
        # Hinweis: folium.Marker() braucht unten explizit icon=folium.Icon(...),
        # weil Leaflets automatische Pfaderkennung fuer den jsdelivr-CDN-Link
        # eine kaputte Bild-URL baut (fehlender "/images/"-Teil) -- ohne das
        # erscheint ein kaputtes Bild-Icon mit sichtbarem Alt-Text auf der Karte.
        karte = folium.Map(
            location=[geo["breitengrad"], geo["laengengrad"]],
            zoom_start=7,
            max_zoom=7,
            tiles="CartoDB positron",
        )

        karten_caption = ""

        if not kommende:
            st.info("Keine Vorhersagedaten für die nächsten 24 Stunden verfügbar.")
            # Trotzdem den Ort markieren
            folium.Marker(
                [geo["breitengrad"], geo["laengengrad"]],
                tooltip=marker_text,
                icon=folium.Icon(color="blue", icon="cloud", prefix="fa"),
            ).add_to(karte)
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
            # FLAECHIGE DARSTELLUNG (Gitter-Vorhersage als Heatmap)
            # Open-Meteo liefert keine Radar-Kachelbilder fuer die Zukunft.
            # Als Ersatz holen wir die Vorhersage fuer ein Gitter aus Punkten
            # rund um den Ort und stellen sie als weiche Heatmap dar -- das
            # wirkt aehnlich flaechig wie das Radar bei "Vergangenheit",
            # ist aber eine interpolierte Vorhersage, kein Kamerabild.
            # ─────────────────────────────────────
            with st.spinner("Lade Flächenvorhersage..."):
                try:
                    gitter = gitter_daten_abrufen(
                        geo["breitengrad"], geo["laengengrad"]
                    )
                except RuntimeError:
                    gitter = {}

            zeit_schluessel = aktive_stunde["zeit"].strftime("%Y-%m-%dT%H:%M")
            gitter_punkte = gitter.get(zeit_schluessel, [])
            heat_daten = [
                [lat, lon, wert] for lat, lon, wert in gitter_punkte if wert > 0.05
            ]
            if heat_daten:
                HeatMap(
                    heat_daten,
                    radius=35,
                    blur=25,
                    min_opacity=0.15,
                    max_zoom=7,
                    gradient={
                        "0.0": "#cfe3f5",
                        "0.3": "#8fc1e8",
                        "0.6": "#4a90d9",
                        "1.0": "#042c53",
                    },
                ).add_to(karte)

            # ─────────────────────────────────────
            # KREIS-DARSTELLUNG nach Regenmenge
            # Farbe: fliessend von hellblau (wenig) zu tiefem Dunkelblau (viel).
            # Groesse: waechst mit der Menge.
            # Kein Regen: winziger, fast unsichtbarer Punkt.
            # ─────────────────────────────────────
            def _kreis_eigenschaften(menge):
                """
                Berechnet Radius, Farbe und Deckkraft eines Kreis-Markers
                passend zu einer Regenmenge. Farbe wird zwischen Hellblau
                (wenig Regen) und Tiefblau (viel Regen) interpoliert.

                Parameter:
                    menge (float): Niederschlagsmenge in mm

                Rückgabe:
                    tuple: (radius, farbe, deckkraft)
                        radius (int): Kreisradius in Pixeln
                        farbe (str): Farbe als Hex-Code
                        deckkraft (float): Deckkraft zwischen 0.0 und 1.0
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
                """
                Übersetzt eine Regenmenge in eine lesbare Beschreibung.

                Parameter:
                    menge (float): Niederschlagsmenge in mm

                Rückgabe:
                    str: Beschreibung der Regenstärke (z. B. "leichter Regen")
                """
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
                icon=folium.Icon(color="blue", icon="cloud", prefix="fa"),
            ).add_to(karte)

            karten_caption = (
                f"Vorhersage für {gewaehltes_label} Uhr: **{mm:.1f} mm** "
                f"({_stufe_text(mm)}) • Fläche = Gitter-Vorhersage rund um den "
                f"Ort, keine Radaraufnahme • Quelle: Open-Meteo"
            )

        # Karte anzeigen. Fester key gegen Flackern.
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