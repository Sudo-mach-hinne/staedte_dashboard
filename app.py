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
# ─────────────────────────────────────────────
st.set_page_config(page_title="City Weather Dashboard", layout="wide")

# ─────────────────────────────────────────────
# WEATHER ICONS FONT
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
hintergrund_css = "background: linear-gradient(170deg, #a8d8ea 0%, #87ceeb 35%, #b0d4e8 55%, #f7c59f 78%, #f4a574 92%, #e8856a 100%);"

if os.path.exists("Clouds_background.jpg"):
    with open("Clouds_background.jpg", "rb") as f:
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
    section[data-testid="stSidebar"] {{
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(10px);
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
# DATENBANKINITIALISIERUNG
# ─────────────────────────────────────────────
datenbank.initialisiere_datenbank()

BEISPIELSTAEDTE = ["Leipzig", "Tokio", "New York City"]

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
# ─────────────────────────────────────────────
col_input, col_button = st.columns([4, 1])
with col_input:
    neue_stadt = st.text_input(
        "Füge Städte hinzu, vergleiche das Wetter und behalte die nächsten Tage im Blick.",
        placeholder="z. B. London, Oslo, Zürich ...",
        key="stadtname_input",
        on_change=lambda: st.session_state.update({"hinzufuegen": True})
    )
    st.caption("💡 Tipp: Bei häufigen Städtenamen einfach präziser suchen, z. B. 'Halle (Saale)' statt 'Halle'.")
with col_button:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Hinzufügen") or st.session_state.get("hinzufuegen"):
        st.session_state["hinzufuegen"] = False
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
# ─────────────────────────────────────────────
if st.session_state.staedte_liste:
    st.divider()
    st.markdown("### 🗺️ Städte auf der Weltkarte")
    st.caption("📍 Klicke auf einen Stadtpin, um aktuelle Wetterdaten sowie Länderinformationen anzuzeigen.")
    karte = folium.Map(
        location=[20, 0],
        zoom_start=3,
        tiles="CartoDB positron",
        min_zoom=3,
        max_bounds=True
    )   
    karte.options["maxBounds"] = [[-90, -180], [90, 180]]
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
    st.divider()
# ─────────────────────────────────────────────
# AUSWERTUNG
# ─────────────────────────────────────────────
st.markdown("### 🌡️ Deine Städte im Vergleich")
if len(st.session_state.staedte_liste) > 1:
    
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
