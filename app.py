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

# ─────────────────────────────────────────────
# SEITENKONFIGURATION
# Muss der allererste Streamlit-Befehl sein.
# layout="wide" nutzt die volle Browserbreite.
# ─────────────────────────────────────────────
st.set_page_config(page_title="City Weather Dashboard", layout="wide")

# ─────────────────────────────────────────────
# WEATHER ICONS FONT
# Lädt die Weather Icons Bibliothek von einem
# externen CDN (cdnjs). Damit können Wetter-
# symbole per CSS-Klasse eingebunden werden.
# ─────────────────────────────────────────────
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.10/css/weather-icons.min.css">
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CSS-STYLING
# Setzt den Hintergrundverlauf (Pfirsich -> Rosa
# -> Hellblau), gestaltet die Seitenleiste
# halbtransparent und gibt Buttons und Metriken
# ein einheitliches Aussehen.
# ─────────────────────────────────────────────
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #FFDAB9 0%, #FFB6C1 50%, #ADD8E6 100%);
    }
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(10px);
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.5);
        border-radius: 12px;
        padding: 10px;
    }
    h1, h2, h3 {
        color: #5a3e6b;
    }
    .stButton > button {
        background: rgba(255, 255, 255, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 8px;
        color: #5a3e6b;
    }
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.9);
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATENBANKINITIALISIERUNG
# Legt die SQLite-Tabellen an, falls sie noch
# nicht existieren. Wird bei jedem App-Start
# aufgerufen -- ist sicher, da CREATE TABLE IF
# NOT EXISTS verwendet wird.
# ─────────────────────────────────────────────
datenbank.initialisiere_datenbank()

# ─────────────────────────────────────────────
# BEISPIELSTÄDTE
# Diese Städte werden beim ersten App-Start
# automatisch geladen, damit die App nicht leer
# erscheint. Kann beliebig angepasst werden.
# ─────────────────────────────────────────────
BEISPIELSTAEDTE = ["Leipzig", "Berlin", "Hamburg"]

# ─────────────────────────────────────────────
# SESSION STATE
# st.session_state speichert Werte über mehrere
# Streamlit-Reloads hinweg. Ohne session_state
# würde die Städteliste bei jeder Interaktion
# zurückgesetzt.
# Beim ersten Aufruf wird die Liste mit den
# Beispielstädten befüllt.
# ─────────────────────────────────────────────
if "staedte_liste" not in st.session_state:
    st.session_state.staedte_liste = []
    for beispiel in BEISPIELSTAEDTE:
        try:
            # Koordinaten über Geocoding API holen
            geo = api_client.koordinaten_abrufen(beispiel)
            # Stadt in Datenbank speichern (INSERT OR IGNORE)
            datenbank.stadt_einfuegen(
                geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
            )
            # Stadt zur Anzeigeliste hinzufügen
            if geo["name"] not in st.session_state.staedte_liste:
                st.session_state.staedte_liste.append(geo["name"])
        except RuntimeError:
            # Wenn eine Beispielstadt nicht gefunden wird, einfach überspringen
            pass

# ─────────────────────────────────────────────
# SEITENTITEL
# ─────────────────────────────────────────────
st.title("🌍 City Weather Dashboard")

# ─────────────────────────────────────────────
# STADTSUCHE
# Zwei Spalten: Eingabefeld (breit) und Button
# (schmal). Bei Klick auf "Hinzufügen" wird:
# 1. Die Stadt über die Geocoding API gesucht
# 2. In der Datenbank gespeichert
# 3. Zur Anzeigeliste hinzugefügt
# 4. Die Seite neu geladen (st.rerun)
# ─────────────────────────────────────────────
col_input, col_button = st.columns([4, 1])
with col_input:
    neue_stadt = st.text_input("Stadt hinzufügen", placeholder="z. B. München, Paris, Wien ...")
with col_button:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Hinzufügen"):
        if not neue_stadt.strip():
            st.error("Bitte einen Stadtnamen eingeben.")
        elif neue_stadt.strip() in st.session_state.staedte_liste:
            st.warning(f"{neue_stadt} ist bereits in der Liste.")
        else:
            try:
                with st.spinner(f"{neue_stadt} wird gesucht..."):
                    geo = api_client.koordinaten_abrufen(neue_stadt.strip())
                datenbank.stadt_einfuegen(
                    geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
                )
                if geo["name"] not in st.session_state.staedte_liste:
                    st.session_state.staedte_liste.append(geo["name"])
                st.rerun()
            except RuntimeError as fehler:
                st.error(str(fehler))

st.divider()

# ─────────────────────────────────────────────
# STÄDTEANZEIGE
# Für jede Stadt in der Liste wird eine Spalte
# angezeigt. Jede Spalte enthält:
# - Entfernen-Button
# - Aktuelles Wetter mit Icon
# - Temperatur und Wind als Metriken
# - Durchschnittstemperatur aus allen Abrufen
# - 7-Tage-Prognose mit Icons
#
# Die Wetterdaten werden bei jeder Anzeige neu
# von der API abgerufen und in der Datenbank
# gespeichert, um einen Verlauf aufzubauen.
# ─────────────────────────────────────────────
if not st.session_state.staedte_liste:
    st.info("Noch keine Städte hinzugefügt.")
else:
    # Eine Spalte pro Stadt
    cols = st.columns(len(st.session_state.staedte_liste))
    staedte_db = datenbank.alle_staedte()

    for i, stadtname in enumerate(st.session_state.staedte_liste):
        # Stadt aus Datenbank holen (für ID und Koordinaten)
        stadt = next((s for s in staedte_db if s["name"] == stadtname), None)
        if not stadt:
            continue

        with cols[i]:
            # Entfernen-Button -- entfernt Stadt nur aus der Anzeigeliste,
            # nicht aus der Datenbank
            if st.button(f"✕ {stadtname}", key=f"entfernen_{stadtname}"):
                st.session_state.staedte_liste.remove(stadtname)
                st.rerun()

            try:
                # Aktuelles Wetter und Prognose von API abrufen
                wetter = api_client.wetter_aktuell_abrufen(
                    stadt["breitengrad"], stadt["laengengrad"]
                )
                prognose = api_client.prognose_abrufen(
                    stadt["breitengrad"], stadt["laengengrad"]
                )

                # Aktuellen Wetterdatensatz in Datenbank speichern
                datenbank.wetterdaten_speichern(
                    stadt["id"],
                    wetter["temperatur"],
                    wetter["windgeschwindigkeit"],
                    wetter["niederschlag"],
                    wetter["wettercode"],
                )

                # Prognosedaten für alle 7 Tage speichern
                for tag in prognose:
                    datenbank.prognose_speichern(
                        stadt["id"],
                        tag["datum"],
                        tag["temperatur_min"],
                        tag["temperatur_max"],
                        tag["niederschlag"],
                        tag["wettercode"],
                    )

                # ── Aktuelles Wetter anzeigen ──
                st.subheader(f"{stadtname}")
                st.caption(f"{stadt['land']}")

                # Wettericon aus WMO-Wettercode bestimmen
                icon_klasse = logik.wettercode_zu_icon(wetter["wettercode"])
                st.markdown(
                    f'<i class="{icon_klasse}" style="font-size: 3rem; color: #f0a500;"></i>',
                    unsafe_allow_html=True
                )

                # Temperatur und Wind als Streamlit-Metriken
                st.metric("Temperatur", f"{wetter['temperatur']} °C")
                st.metric("Wind", f"{wetter['windgeschwindigkeit']} km/h")

                # Durchschnittstemperatur aus allen gespeicherten Abrufen
                # berechnet via pandas in logik.py
                wetterdaten_gespeichert = datenbank.wetterdaten_nach_stadt(stadt["id"])
                durchschnitt = logik.durchschnittstemperatur(wetterdaten_gespeichert)
                if durchschnitt:
                    st.caption(f"Ø Temperatur: {durchschnitt} °C")

                st.divider()

                # ── 7-Tage-Prognose ──
                st.markdown("**7-Tage-Prognose**")
                for tag in prognose:
                    # Icon für jeden Prognosetag
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
                # API-Fehler werden pro Stadt angezeigt --
                # ein Fehler bricht nicht die anderen Städte ab
                st.error(f"{stadtname}: {str(fehler)}")