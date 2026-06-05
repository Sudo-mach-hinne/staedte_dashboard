"""
Modulname: app.py
Beschreibung: Streamlit-Frontend -- City Weather Dashboard
Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""
import streamlit as st
import datenbank
import api_client
import logik
from streamlit_folium import st_folium
import folium
import base64
import os

# ─────────────────────────────────────────────
# SEITENKONFIGURATION
# Muss der allererste Streamlit-Befehl sein.
# layout="wide" nutzt die volle Browserbreite.
# ─────────────────────────────────────────────
st.set_page_config(page_title="City Weather Dashboard", layout="wide")

# ─────────────────────────────────────────────
# WEATHER ICONS FONT
# Lädt die Weather Icons Bibliothek von einem
# externen CDN (cdnjs.cloudflare.com).
# Ermöglicht Wettersymbole per CSS-Klasse,
# z. B. "wi wi-day-sunny" für eine Sonne.
# ─────────────────────────────────────────────
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.10/css/weather-icons.min.css">
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HINTERGRUNDBILD
# Wird als Base64 eingebettet damit Streamlit
# es nicht blockiert. Datei Clouds_background.jpg
# muss im Projektordner liegen.
# ─────────────────────────────────────────────
if os.path.exists("Clouds_background.jpg"):
    with open("Clouds_background.jpg", "rb") as f:
        bild_b64 = base64.b64encode(f.read()).decode()
    hintergrund_css = f'background-image: url("data:image/jpeg;base64,{bild_b64}"); background-size: cover; background-position: center; background-attachment: fixed;'
else:
    hintergrund_css = "background: linear-gradient(135deg, #FFDAB9 0%, #FFB6C1 50%, #ADD8E6 100%);"

# ─────────────────────────────────────────────
# CSS-STYLING
# Individuelles Design per injiziertem CSS.
# .stApp         -- Hintergrundbild oder Verlauf
# .stApp::before -- halbtransparentes Overlay
# stSidebar      -- halbtransparente Seitenleiste
# .stMetric      -- abgerundete Metrik-Kacheln
# h1/h2/h3       -- Titelfarbe lila
# .stButton      -- abgerundete, halbtransp. Buttons
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
        background: rgba(255, 255, 255, 0.35);
        z-index: 0;
    }}
    section[data-testid="stSidebar"] {{
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(10px);
    }}
    .stMetric {{
        background: rgba(255, 255, 255, 0.5);
        border-radius: 12px;
        padding: 10px;
    }}
    h1, h2, h3 {{
        color: #5a3e6b;
        font-size: 1.6rem !important;
    }}
    h1 {{
        font-size: 2rem !important;
    }}
    p, label, div[data-testid="stCaptionContainer"] {{
        font-size: 15px !important;
    }}
    .stButton > button {{
        background: rgba(255, 255, 255, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 8px;
        color: #5a3e6b;
        font-size: 15px !important;
    }}
    .stButton > button:hover {{
        background: rgba(255, 255, 255, 0.9);
    }}
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATENBANKINITIALISIERUNG
# Legt alle SQLite-Tabellen an, falls sie noch
# nicht existieren (CREATE TABLE IF NOT EXISTS).
# Wird bei jedem App-Start aufgerufen -- sicher,
# weil keine Daten überschrieben werden.
# ─────────────────────────────────────────────
datenbank.initialisiere_datenbank()

# ─────────────────────────────────────────────
# BEISPIELSTÄDTE
# Beim ersten App-Start werden diese Städte
# automatisch geladen, damit die App nicht leer
# erscheint. Liste kann beliebig angepasst werden.
# ─────────────────────────────────────────────
BEISPIELSTAEDTE = ["Leipzig", "Tokio", "Prag"]

# ─────────────────────────────────────────────
# SESSION STATE -- STÄDTELISTE
# st.session_state speichert Werte über mehrere
# Streamlit-Reloads hinweg. Ohne session_state
# würde die Städteliste bei jeder Interaktion
# zurückgesetzt werden.
#
# Beim allerersten Aufruf (session_state noch
# leer) werden die Beispielstädte über die
# Geocoding API gesucht, in der Datenbank
# gespeichert und zur Anzeigeliste hinzugefügt.
# ─────────────────────────────────────────────
if "staedte_liste" not in st.session_state:
    st.session_state.staedte_liste = []
    for beispiel in BEISPIELSTAEDTE:
        try:
            treffer = api_client.koordinaten_abrufen(beispiel)
            if treffer:
                geo = treffer[0]
                datenbank.stadt_einfuegen(
                    geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
                )
                if geo["name"] not in st.session_state.staedte_liste:
                    st.session_state.staedte_liste.append(geo["name"])
        except RuntimeError:
            pass

# ─────────────────────────────────────────────
# SEITENTITEL
# ─────────────────────────────────────────────
st.title("🌍 City Weather Dashboard")

# ─────────────────────────────────────────────
# STADTSUCHE
# Zwei Spalten: Eingabefeld (breit) und Button
# (schmal). Bei Klick auf "Hinzufügen" wird:
# 1. Eingabe auf leer geprüft
# 2. Geprüft ob Stadt bereits in der Liste
# 3. Geocoding API aufgerufen (Koordinaten holen)
# 4. Bei einem Treffer: direkt speichern
# 5. Bei mehreren Treffern: Auswahl anzeigen
# 6. Seite neu laden (st.rerun)
# ─────────────────────────────────────────────
col_input, col_button = st.columns([4, 1])
with col_input:
    neue_stadt = st.text_input(
        "Füge Städte hinzu, vergleiche das Wetter und behalte die nächsten Tage im Blick.",
        placeholder="z. B. London, Oslo, Zürich ..."
    )
    st.caption("💡 Tipp: Bei häufigen Städtenamen einfach präziser suchen — z. B. 'Halle (Saale)' statt 'Halle'.")
with col_button:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Hinzufügen"):
        if not neue_stadt.strip():
            st.warning("🌍 Bitte gib einen Stadtnamen ein!")
        elif neue_stadt.strip() in st.session_state.staedte_liste:
            st.warning(f"🏙️ {neue_stadt} ist bereits in deiner Liste!")
        else:
            try:
                with st.spinner(f"🔍 Suche nach {neue_stadt}..."):
                    treffer = api_client.koordinaten_abrufen(neue_stadt.strip())
                if len(treffer) == 1:
                    geo = treffer[0]
                    datenbank.stadt_einfuegen(
                        geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
                    )
                    if geo["name"] not in st.session_state.staedte_liste:
                        st.session_state.staedte_liste.append(geo["name"])
                    st.rerun()
                else:
                    st.session_state.treffer = treffer
            except RuntimeError:
                st.error("😢 Oh no! Diese Stadt ist unbekannt. Vielleicht ein Tippfehler?")

# ─────────────────────────────────────────────
# AUSWAHL BEI MEHREREN TREFFERN
# Wenn die API mehrere Städte mit gleichem Namen
# findet (z. B. "Frankfurt" in Deutschland und
# USA), wird eine Auswahl als Buttons angezeigt.
# Nach der Auswahl wird treffer geleert und
# die Seite neu geladen.
# ─────────────────────────────────────────────
if "treffer" in st.session_state and st.session_state.treffer:
    st.info("🌍 Mehrere Städte gefunden – welche meinst du?")
    for geo in st.session_state.treffer:
        label = f"{geo['name']} — {geo['region']}, {geo['land']}"
        if st.button(label, key=f"treffer_{geo['breitengrad']}_{geo['laengengrad']}"):
            datenbank.stadt_einfuegen(
                geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
            )
            if geo["name"] not in st.session_state.staedte_liste:
                st.session_state.staedte_liste.append(geo["name"])
            st.session_state.treffer = []
            st.rerun()

st.divider()

# ─────────────────────────────────────────────
# STÄDTEANZEIGE
# Für jede Stadt in der Anzeigeliste wird eine
# Spalte nebeneinander angezeigt. Jede Spalte
# enthält:
# - Entfernen-Button (nur aus Anzeigeliste,
#   nicht aus Datenbank)
# - Aktuelles Wetter mit Wettericon
# - Temperatur und Wind als Metriken
# - Ø Temperatur aus allen bisherigen Abrufen
# - 7-Tage-Prognose mit Icons, Min/Max-Werten
#
# Wetterdaten werden bei jeder Anzeige neu
# von der API abgerufen und in der Datenbank
# gespeichert -- so entsteht ein Verlauf.
# ─────────────────────────────────────────────
if not st.session_state.staedte_liste:
    st.info("Noch keine Städte hinzugefügt.")
else:
    cols = st.columns(len(st.session_state.staedte_liste))
    staedte_db = datenbank.alle_staedte()

    for i, stadtname in enumerate(st.session_state.staedte_liste):
        stadt = next((s for s in staedte_db if s["name"] == stadtname), None)
        if not stadt:
            continue

        with cols[i]:
            if st.button(f"❌ {stadtname}", key=f"entfernen_{stadtname}"):
                st.session_state.staedte_liste.remove(stadtname)
                st.rerun()

            try:
                wetter = api_client.wetter_aktuell_abrufen(
                    stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
                )
                prognose = api_client.prognose_abrufen(
                    stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
                )
                if len(prognose) < 7:
                    st.warning("⚠️ Technische Störung, Wetterdienst funktioniert eingeschränkt!")

                datenbank.wetterdaten_speichern(
                    stadt["id"],
                    wetter["temperatur"],
                    wetter["windgeschwindigkeit"],
                    wetter["niederschlag"],
                    wetter["wettercode"],
                )

                for tag in prognose:
                    datenbank.prognose_speichern(
                        stadt["id"],
                        tag["datum"],
                        tag["temperatur_min"],
                        tag["temperatur_max"],
                        tag["niederschlag"],
                        tag["wettercode"],
                    )

                st.subheader(f"{stadtname}")
                st.caption(f"{stadt['land']}")

                icon_klasse = logik.wettercode_zu_icon(wetter["wettercode"])
                st.markdown(
                    f'<i class="{icon_klasse}" style="font-size: 3rem; color: #f0a500;"></i>',
                    unsafe_allow_html=True
                )

                st.metric("Temperatur", f"{wetter['temperatur']} °C")
                st.metric("Wind", f"{wetter['windgeschwindigkeit']} km/h")

                wetterdaten_gespeichert = datenbank.wetterdaten_nach_stadt(stadt["id"])
                durchschnitt = logik.durchschnittstemperatur(wetterdaten_gespeichert)
                if durchschnitt:
                    st.caption(f"Ø Temperatur: {durchschnitt} °C")

                st.divider()

                st.markdown("**7-Tage-Prognose**")
                for tag in prognose:
                    icon_klasse = logik.wettercode_zu_icon(tag["wettercode"])
                    pcol1, pcol2, pcol3 = st.columns([2, 1, 2])
                    with pcol1:
                        st.caption(tag["datum"])
                    with pcol2:
                        st.markdown(
                            f'<i class="{icon_klasse}" style="font-size: 1.2rem; color: #f0a500;"></i>',
                            unsafe_allow_html=True
                        )
                    with pcol3:
                        st.caption(f"↑{tag['temperatur_max']}° ↓{tag['temperatur_min']}°")

            except RuntimeError as fehler:
                st.error(f"{stadtname}: {str(fehler)}")

# ─────────────────────────────────────────────
# WELTKARTE
# Zeigt alle aktuellen Städte als Pins auf einer
# interaktiven Weltkarte. Klick auf Pin öffnet
# Popup mit Wetterdaten und Länderinformationen.
# ─────────────────────────────────────────────
if st.session_state.staedte_liste:
    st.divider()
    st.markdown("### 🗺️ Städte auf der Weltkarte")

    karte = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
    staedte_db = datenbank.alle_staedte()

    for stadtname in st.session_state.staedte_liste:
        stadt = next((s for s in staedte_db if s["name"] == stadtname), None)
        if not stadt:
            continue
        try:
            wetter = api_client.wetter_aktuell_abrufen(
                stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
            )
            laender = api_client.laenderdaten_abrufen(stadt["land"])

            popup_text = f"""
            <b>{stadtname}</b><br>
            🌡️ {wetter['temperatur']} °C &nbsp;|&nbsp; 💨 {wetter['windgeschwindigkeit']} km/h<br>
            🌧️ Niederschlag: {wetter['niederschlag']} mm<br>
            """
            if laender:
                popup_text += f"""
            <hr style='margin:4px 0'>
            🏛️ Hauptstadt: {laender['hauptstadt']}<br>
            💶 Währung: {laender['waehrung']}<br>
            🗣️ Sprache(n): {laender['sprachen']}
            """

            folium.Marker(
                location=[stadt["breitengrad"], stadt["laengengrad"]],
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=stadtname,
                icon=folium.Icon(color="purple", icon="cloud", prefix="fa"),
            ).add_to(karte)

        except RuntimeError:
            pass

    st_folium(karte, use_container_width=True, height=400)

# ─────────────────────────────────────────────
# AUSWERTUNG: Sonnigste, verregnetste, wärmste
# und kälteste Stadt. Wird nur angezeigt wenn
# mindestens 2 Städte in der Liste sind.
# ─────────────────────────────────────────────
if len(st.session_state.staedte_liste) > 1:
    st.divider()
    staedte_db = datenbank.alle_staedte()

    sonnigste = None
    verregnetste = None
    waermste = None
    kaelteste = None
    min_wettercode = 999
    max_niederschlag = -1
    max_temp = -999
    min_temp = 999

    for stadtname in st.session_state.staedte_liste:
        stadt = next((s for s in staedte_db if s["name"] == stadtname), None)
        if not stadt:
            continue
        try:
            wetter = api_client.wetter_aktuell_abrufen(
                stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
            )
            prognose = api_client.prognose_abrufen(
                stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
            )
            if wetter["wettercode"] < min_wettercode:
                min_wettercode = wetter["wettercode"]
                sonnigste = (stadtname, wetter["temperatur"])

            gesamt = sum(tag["niederschlag"] for tag in prognose)
            if gesamt > max_niederschlag:
                max_niederschlag = gesamt
                verregnetste = (stadtname, gesamt, wetter["temperatur"])

            avg_max = sum(tag["temperatur_max"] for tag in prognose) / len(prognose)
            if avg_max > max_temp:
                max_temp = avg_max
                waermste = (stadtname, round(avg_max, 1))

            avg_min = sum(tag["temperatur_min"] for tag in prognose) / len(prognose)
            if avg_min < min_temp:
                min_temp = avg_min
                kaelteste = (stadtname, round(avg_min, 1))

        except RuntimeError:
            pass

    if sonnigste:
        st.success(f"☀️ Das sonnigste Wetter hat **{sonnigste[0]}** – aktuell {sonnigste[1]} °C.")
    if verregnetste:
        st.info(f"🌧️ Am meisten regnet es in **{verregnetste[0]}** – {round(verregnetste[1], 1)} mm Niederschlag, aktuell {verregnetste[2]} °C.")
    if waermste:
        st.warning(f"🥵 Am wärmsten ist es in **{waermste[0]}** – Ø Höchsttemperatur {waermste[1]} °C.")
    if kaelteste:
        st.info(f"🥶 Am kältesten ist es in **{kaelteste[0]}** – Ø Tiefsttemperatur {kaelteste[1]} °C.")
