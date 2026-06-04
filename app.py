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
# externen CDN (cdnjs.cloudflare.com).
# Ermöglicht Wettersymbole per CSS-Klasse,
# z. B. "wi wi-day-sunny" für eine Sonne.
# ─────────────────────────────────────────────
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.10/css/weather-icons.min.css">
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CSS-STYLING
# Individuelles Design per injiziertem CSS.
# .stApp         -- Hintergrundverlauf der App
# stSidebar      -- halbtransparente Seitenleiste
# .stMetric      -- abgerundete Metrik-Kacheln
# h1/h2/h3       -- Titelfarbe lila
# .stButton      -- abgerundete, halbtransp. Buttons
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
BEISPIELSTAEDTE = ["Leipzig", "Berlin", "Hamburg"]

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
            # Geocoding API gibt eine Liste von Treffern zurück
            treffer = api_client.koordinaten_abrufen(beispiel)
            if treffer:
                # Ersten Treffer nehmen (relevantester Treffer)
                geo = treffer[0]
                # Stadt in Datenbank speichern (INSERT OR IGNORE --
                # kein Fehler wenn Stadt schon existiert)
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
# 1. Eingabe auf leer geprüft
# 2. Geprüft ob Stadt bereits in der Liste
# 3. Geocoding API aufgerufen (Koordinaten holen)
# 4. Bei einem Treffer: direkt speichern
# 5. Bei mehreren Treffern: Auswahl anzeigen
# 6. Seite neu laden (st.rerun)
# ─────────────────────────────────────────────
col_input, col_button = st.columns([4, 1])
with col_input:
    neue_stadt = st.text_input("Stadt hinzufügen", placeholder="z. B. München, Paris, Wien ...")
    # Hinweis für häufige Städtenamen
    st.caption("💡 Tipp: Bei häufigen Städtenamen einfach präziser suchen — z. B. 'Halle (Saale)' statt 'Halle'.")
with col_button:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Hinzufügen"):
        if not neue_stadt.strip():
            # Leere Eingabe abfangen
            st.warning("🌍 Gib einen Stadtnamen ein, dann suchen wir sie für dich!")
        elif neue_stadt.strip() in st.session_state.staedte_liste:
            # Doppelte Einträge verhindern
            st.warning(f"🏙️ {neue_stadt} ist bereits in deiner Liste!")
        else:
            try:
                with st.spinner(f"🔍 Suche nach {neue_stadt}..."):
                    # Geocoding API aufrufen -- gibt Liste von Treffern zurück
                    treffer = api_client.koordinaten_abrufen(neue_stadt.strip())
                if len(treffer) == 1:
                    # Genau ein Treffer -- direkt speichern
                    geo = treffer[0]
                    datenbank.stadt_einfuegen(
                        geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
                    )
                    if geo["name"] not in st.session_state.staedte_liste:
                        st.session_state.staedte_liste.append(geo["name"])
                    st.rerun()
                else:
                    # Mehrere Treffer -- im session_state zwischenspeichern
                    # damit die Auswahl im nächsten Block angezeigt werden kann
                    st.session_state.treffer = treffer
            except RuntimeError:
                # Freundliche Fehlermeldung bei unbekannter Stadt
                st.error("😢 Oh no! Diese Stadt kennen wir leider nicht. Vielleicht ein Tippfehler?")

# ─────────────────────────────────────────────
# AUSWAHL BEI MEHREREN TREFFERN
# Wenn die API mehrere Städte mit gleichem Namen
# findet (z. B. "Frankfurt" in Deutschland und
# USA), wird eine Auswahl als Buttons angezeigt.
# Nach der Auswahl wird treffer geleert und
# die Seite neu geladen.
# ─────────────────────────────────────────────
if "treffer" in st.session_state and st.session_state.treffer:
    st.info("🌍 Wir haben mehrere Städte gefunden – welche meinst du?")
    for geo in st.session_state.treffer:
        # Label zeigt Name, Region und Land zur eindeutigen Identifikation
        label = f"{geo['name']} — {geo['region']}, {geo['land']}"
        if st.button(label, key=f"treffer_{geo['breitengrad']}_{geo['laengengrad']}"):
            datenbank.stadt_einfuegen(
                geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
            )
            if geo["name"] not in st.session_state.staedte_liste:
                st.session_state.staedte_liste.append(geo["name"])
            # Trefferliste leeren nach Auswahl
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
    # Eine Spalte pro Stadt nebeneinander
    cols = st.columns(len(st.session_state.staedte_liste))
    # Alle Städte aus Datenbank holen (für ID und Koordinaten)
    staedte_db = datenbank.alle_staedte()

    for i, stadtname in enumerate(st.session_state.staedte_liste):
        # Passenden Datenbankeintrag zur Stadt suchen
        stadt = next((s for s in staedte_db if s["name"] == stadtname), None)
        if not stadt:
            continue

        with cols[i]:
            # Entfernen-Button -- löscht nur aus der Anzeigeliste,
            # Datenbankdaten bleiben erhalten
            if st.button(f"✕ {stadtname}", key=f"entfernen_{stadtname}"):
                st.session_state.staedte_liste.remove(stadtname)
                st.rerun()

            try:
                # Aktuelles Wetter von Open-Meteo abrufen
                wetter = api_client.wetter_aktuell_abrufen(
                    stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
                )
                # 7-Tage-Prognose von Open-Meteo abrufen
                prognose = api_client.prognose_abrufen(
                    stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
                )

                # Aktuellen Wetterdatensatz in Datenbank speichern
                # (baut Verlauf für Durchschnittsberechnung auf)
                datenbank.wetterdaten_speichern(
                    stadt["id"],
                    wetter["temperatur"],
                    wetter["windgeschwindigkeit"],
                    wetter["niederschlag"],
                    wetter["wettercode"],
                )

                # Alle 7 Prognosetage in Datenbank speichern
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

                # WMO-Wettercode in Weather-Icons CSS-Klasse umwandeln
                # (Funktion liegt in logik.py)
                icon_klasse = logik.wettercode_zu_icon(wetter["wettercode"])
                st.markdown(
                    f'<i class="{icon_klasse}" style="font-size: 3rem; color: #f0a500;"></i>',
                    unsafe_allow_html=True
                )

                # Temperatur und Wind als Streamlit-Metriken anzeigen
                st.metric("Temperatur", f"{wetter['temperatur']} °C")
                st.metric("Wind", f"{wetter['windgeschwindigkeit']} km/h")

                # Durchschnittstemperatur aus allen gespeicherten Abrufen
                # berechnet mit pandas in logik.durchschnittstemperatur()
                wetterdaten_gespeichert = datenbank.wetterdaten_nach_stadt(stadt["id"])
                durchschnitt = logik.durchschnittstemperatur(wetterdaten_gespeichert)
                if durchschnitt:
                    st.caption(f"Ø Temperatur: {durchschnitt} °C")

                st.divider()

                # ── 7-Tage-Prognose ──
                st.markdown("**7-Tage-Prognose**")
                for tag in prognose:
                    # Icon für jeden einzelnen Prognosetag bestimmen
                    icon_klasse = logik.wettercode_zu_icon(tag["wettercode"])
                    # Drei Spalten: Datum | Icon | Temperatur
                    pcol1, pcol2, pcol3 = st.columns([2, 1, 2])
                    with pcol1:
                        st.caption(tag["datum"])
                    with pcol2:
                        st.markdown(
                            f'<i class="{icon_klasse}" style="font-size: 1.2rem; color: #f0a500;"></i>',
                            unsafe_allow_html=True
                        )
                    with pcol3:
                        # Höchst- und Tiefstwert des Tages
                        st.caption(f"↑{tag['temperatur_max']}° ↓{tag['temperatur_min']}°")

            except RuntimeError as fehler:
                # API-Fehler werden pro Stadt einzeln angezeigt --
                # ein Fehler bei einer Stadt bricht die anderen nicht ab
                st.error(f"{stadtname}: {str(fehler)}")

# ─────────────────────────────────────────────
# AUSWERTUNG: Sonnigste und verregnetste Stadt
# Wird nur angezeigt wenn mindestens 2 Städte
# in der Liste sind. Vergleicht:
# - Sonnigste Stadt: niedrigster WMO-Wettercode
#   (0 = klar, höhere Werte = schlechter)
# - Verregnetste Stadt: höchster Gesamtniederschlag
#   aus der 7-Tage-Prognose
# ─────────────────────────────────────────────
if len(st.session_state.staedte_liste) > 1:
    st.divider()
    staedte_db = datenbank.alle_staedte()

    sonnigste = None
    verregnetste = None
    min_wettercode = 999
    max_niederschlag = -1

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
            # Sonnigste Stadt = niedrigster aktueller Wettercode
            if wetter["wettercode"] < min_wettercode:
                min_wettercode = wetter["wettercode"]
                sonnigste = stadtname
            # Verregnetste Stadt = höchster Gesamtniederschlag in Prognose
            gesamt = sum(tag["niederschlag"] for tag in prognose)
            if gesamt > max_niederschlag:
                max_niederschlag = gesamt
                verregnetste = stadtname
        except RuntimeError:
            # Fehler bei einzelner Stadt ignorieren
            pass

    if sonnigste:
        st.success(f"☀️ Das sonnigste Wetter hat **{sonnigste}**.")
    if verregnetste:
        st.info(f"🌧️ Am meisten regnet es in **{verregnetste}**.")