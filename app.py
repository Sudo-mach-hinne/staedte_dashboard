"""
Modulname: app.py
Beschreibung: Streamlit-Frontend -- City Weather Dashboard.
Hauptseite: Staedte verwalten, aktuelles Wetter + 7-Tage-Prognose anzeigen, Weltkarte und Staedte-Vergleich.

Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""

# --- Externe Bibliotheken ---
import streamlit as st                      # Web-Frontend
from streamlit_folium import st_folium       # bindet folium-Karten in Streamlit ein
import folium                                # interaktive Karten

# --- Eigene Module ---
import datenbank                             # SQLite-Zugriff (Staedte, Wetter, Prognose)
import api_client                            # API-Aufrufe (Open-Meteo, REST Countries)
import logik                                 # Berechnungen (Vergleich, Durchschnitt, Icons)
import stil                                  # zentrales CSS/Styling (frueher dupliziert)

# ─────────────────────────────────────────────
# SEITENKONFIGURATION
# Muss der erste Streamlit-Befehl sein.
# ─────────────────────────────────────────────
st.set_page_config(page_title="City Weather Dashboard", layout="wide")

# ─────────────────────────────────────────────
# STYLING (Font, Hintergrund, CSS -- ausgelagert in stil.py)
# Eine Zeile statt ~80 Zeilen dupliziertem CSS auf jeder Seite.
# ─────────────────────────────────────────────
stil.lade_css()

# ─────────────────────────────────────────────
# DATENBANKINITIALISIERUNG
# Legt die SQLite-Tabellen an, falls sie noch nicht existieren.
# ─────────────────────────────────────────────
datenbank.initialisiere_datenbank()


# ─────────────────────────────────────────────
# GECACHTE API-WRAPPER
# Streamlit fuehrt das Skript bei JEDER Interaktion komplett neu aus.
# Ohne Cache wuerde jeder Reload neue API-Calls ausloesen. @st.cache_data
# speichert die Antwort und liefert sie fuer 10 Minuten (ttl=600) direkt
# zurueck. Die eigentliche Logik bleibt in api_client.py (streamlit-frei,
# damit die pytest-Tests ohne Streamlit laufen).
# ─────────────────────────────────────────────
@st.cache_data(ttl=600)
def wetter_aktuell_cached(breitengrad, laengengrad, stadtname=None):
    """Gecachter Aufruf von api_client.wetter_aktuell_abrufen()."""
    return api_client.wetter_aktuell_abrufen(breitengrad, laengengrad, stadtname=stadtname)


@st.cache_data(ttl=600)
def prognose_cached(breitengrad, laengengrad, tage=7, stadtname=None):
    """Gecachter Aufruf von api_client.prognose_abrufen()."""
    return api_client.prognose_abrufen(breitengrad, laengengrad, tage=tage, stadtname=stadtname)


# ─────────────────────────────────────────────
# STARTZUSTAND
# Beim allerersten Laden drei Beispielstaedte anlegen, damit die Seite
# nicht leer ist. Laeuft nur einmal pro Session (Pruefung auf session_state).
# ─────────────────────────────────────────────
BEISPIELSTAEDTE = ["Leipzig", "Tokio", "New York City"]

if "staedte_liste" not in st.session_state:
    st.session_state.staedte_liste = []
    for beispiel in BEISPIELSTAEDTE:
        try:
            # Geocoding: Stadtname -> Koordinaten (kann mehrere Treffer liefern)
            treffer = api_client.koordinaten_abrufen(beispiel)
            if treffer:
                geo = treffer[0]   # erster Treffer als Standard
                datenbank.stadt_einfuegen(
                    geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
                )
                if geo["name"] not in st.session_state.staedte_liste:
                    st.session_state.staedte_liste.append(geo["name"])
        except RuntimeError:
            # Falls die Geocoding-API nicht erreichbar ist: Stadt ueberspringen,
            # nicht die ganze App abstuerzen lassen.
            pass

# ─────────────────────────────────────────────
# SEITENTITEL
# ─────────────────────────────────────────────
st.title("🌍 City Weather Dashboard")

# ─────────────────────────────────────────────
# STADTSUCHE
# Texteingabe + Button. on_change setzt ein Flag, damit auch das Druecken
# von Enter (nicht nur der Button-Klick) die Suche ausloest.
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
    st.markdown("<br>", unsafe_allow_html=True)   # kleiner Abstand, damit Button auf Feldhoehe sitzt
    # Suche startet bei Button-Klick ODER gesetztem Enter-Flag
    if st.button("➕ Hinzufügen") or st.session_state.get("hinzufuegen"):
        st.session_state["hinzufuegen"] = False   # Flag sofort zuruecksetzen
        if not neue_stadt.strip():
            st.warning("🌍 Bitte gib einen Stadtnamen ein!")
        elif neue_stadt.strip() in st.session_state.staedte_liste:
            st.warning(f"🏙️ {neue_stadt} ist bereits in deiner Liste!")
        else:
            try:
                with st.spinner(f"🔍 Suche nach {neue_stadt}..."):
                    treffer = api_client.koordinaten_abrufen(neue_stadt.strip())
                if len(treffer) == 1:
                    # Eindeutiger Treffer: direkt uebernehmen
                    geo = treffer[0]
                    datenbank.stadt_einfuegen(
                        geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
                    )
                    if geo["name"] not in st.session_state.staedte_liste:
                        st.session_state.staedte_liste.append(geo["name"])
                    st.rerun()   # Seite neu laden, damit die Stadt sofort erscheint
                else:
                    # Mehrere Treffer: zur Auswahl zwischenspeichern (s. naechster Block)
                    st.session_state.treffer = treffer
            except RuntimeError:
                st.error("😢 Oh no! Diese Stadt ist unbekannt. Vielleicht ein Tippfehler?")

# ─────────────────────────────────────────────
# AUSWAHL BEI MEHREREN TREFFERN
# Wenn die Geocoding-API mehrere Orte gleichen Namens liefert, zeigt sie
# hier zur Auswahl an (z. B. mehrere "Springfield").
# ─────────────────────────────────────────────
if "treffer" in st.session_state and st.session_state.treffer:
    st.info("🌍 Mehrere Städte gefunden – welche meinst du?")
    for geo in st.session_state.treffer:
        label = f"{geo['name']} — {geo['region']}, {geo['land']}"
        # key muss eindeutig sein -> Koordinaten anhaengen
        if st.button(label, key=f"treffer_{geo['breitengrad']}_{geo['laengengrad']}"):
            datenbank.stadt_einfuegen(
                geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
            )
            if geo["name"] not in st.session_state.staedte_liste:
                st.session_state.staedte_liste.append(geo["name"])
            st.session_state.treffer = []   # Auswahl leeren
            st.rerun()

st.divider()

# ─────────────────────────────────────────────
# STÄDTEANZEIGE
# Pro Stadt eine Spalte mit aktuellem Wetter und 7-Tage-Prognose.
# ─────────────────────────────────────────────
if not st.session_state.staedte_liste:
    st.info("Noch keine Städte hinzugefügt.")
else:
    cols = st.columns(len(st.session_state.staedte_liste))
    staedte_db = datenbank.alle_staedte()

    for i, stadtname in enumerate(st.session_state.staedte_liste):
        # passenden DB-Eintrag zur Stadt finden
        stadt = next((s for s in staedte_db if s["name"] == stadtname), None)
        if not stadt:
            continue

        with cols[i]:
            # Entfernen-Button pro Stadt
            if st.button(f"❌ {stadtname}", key=f"entfernen_{stadtname}"):
                st.session_state.staedte_liste.remove(stadtname)
                st.rerun()

            try:
                # Wetter + Prognose ueber die gecachten Wrapper holen
                wetter = wetter_aktuell_cached(
                    stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
                )
                prognose = prognose_cached(
                    stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
                )
                if len(prognose) < 7:
                    st.warning("⚠️ Technische Störung, Wetterdienst funktioniert eingeschränkt!")

                # aktuelle Werte in die DB schreiben (Historie)
                datenbank.wetterdaten_speichern(
                    stadt["id"],
                    wetter["temperatur"],
                    wetter["windgeschwindigkeit"],
                    wetter["niederschlag"],
                    wetter["wettercode"],
                )

                # Prognosetage speichern
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

                # Wettercode -> Icon-CSS-Klasse (weather-icons-Font)
                icon_klasse = logik.wettercode_zu_icon(wetter["wettercode"])
                st.markdown(
                    f'<i class="{icon_klasse}" style="font-size: 3rem; color: #f0a500;"></i>',
                    unsafe_allow_html=True
                )

                st.metric("Temperatur", f"{wetter['temperatur']} °C")
                st.metric("Wind", f"{wetter['windgeschwindigkeit']} km/h")

                # Durchschnitt aus der gespeicherten Historie
                wetterdaten_gespeichert = datenbank.wetterdaten_nach_stadt(stadt["id"])
                durchschnitt = logik.durchschnittstemperatur(wetterdaten_gespeichert)
                if durchschnitt:
                    st.caption(f"Ø Temperatur: {durchschnitt} °C")

                st.divider()

                # 7-Tage-Prognose als kompakte Zeilen (Datum | Icon | Hoch/Tief)
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
                # Wetter-API fuer DIESE Stadt nicht erreichbar -> nur diese Spalte zeigt Fehler
                st.error(f"{stadtname}: {str(fehler)}")

# ─────────────────────────────────────────────
# WELTKARTE
# Alle Staedte als Pins; Klick zeigt Wetter + Laenderinfos im Popup.
# ─────────────────────────────────────────────
if st.session_state.staedte_liste:
    st.divider()
    st.markdown("### 🗺️ Städte auf der Weltkarte")
    st.caption("📍 Klicke auf einen Stadtpin, um aktuelle Wetterdaten sowie Länderinformationen anzuzeigen.")
    karte = folium.Map(
        location=[20, 0],          # Startmittelpunkt
        zoom_start=3,
        tiles="CartoDB positron",  # heller, schlichter Kartenstil
        min_zoom=3,
        max_bounds=True            # nicht endlos rausscrollbar
    )
    karte.options["maxBounds"] = [[-90, -180], [90, 180]]  # auf eine Welt begrenzen
    staedte_db = datenbank.alle_staedte()

    for stadtname in st.session_state.staedte_liste:
        stadt = next((s for s in staedte_db if s["name"] == stadtname), None)
        if not stadt:
            continue
        try:
            wetter = wetter_aktuell_cached(
                stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
            )
            laender = api_client.laenderdaten_abrufen(stadt["land"])

            # Popup-Inhalt zusammenbauen (HTML)
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
            # Pin fuer diese Stadt ueberspringen, Karte trotzdem zeigen
            pass

    st_folium(karte, use_container_width=True, height=400)
    st.divider()

# ─────────────────────────────────────────────
# AUSWERTUNG
# Superlativ-Saetze (sonnigste/verregnetste/waermste/kaelteste Stadt) plus
# Vergleichstabelle. Nur sinnvoll ab 2 Staedten.
# ─────────────────────────────────────────────
st.markdown("### 🌡️ Deine Städte im Vergleich")
if len(st.session_state.staedte_liste) > 1:

    staedte_db = datenbank.alle_staedte()

    # Platzhalter fuer die "Gewinner" jeder Kategorie
    sonnigste = None
    verregnetste = None
    waermste = None
    kaelteste = None
    # Startwerte bewusst extrem, damit der erste echte Wert sie sicher schlaegt
    min_wettercode = 999
    max_niederschlag = -1
    max_temp = -999
    min_temp = 999

    # Daten fuer logik.staedte_vergleich() sammeln (Name + Prognose je Stadt)
    vergleich_daten = []

    for stadtname in st.session_state.staedte_liste:
        stadt = next((s for s in staedte_db if s["name"] == stadtname), None)
        if not stadt:
            continue
        try:
            wetter = wetter_aktuell_cached(
                stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
            )
            prognose = prognose_cached(
                stadt["breitengrad"], stadt["laengengrad"], stadtname=stadtname
            )

            # Prognose fuer die Vergleichstabelle merken
            vergleich_daten.append({"name": stadtname, "prognose": prognose})

            # niedrigster Wettercode = klarster Himmel = "sonnigste"
            if wetter["wettercode"] < min_wettercode:
                min_wettercode = wetter["wettercode"]
                sonnigste = (stadtname, wetter["temperatur"])

            # hoechste Niederschlagssumme ueber die Prognosetage
            gesamt = sum(tag["niederschlag"] for tag in prognose)
            if gesamt > max_niederschlag:
                max_niederschlag = gesamt
                verregnetste = (stadtname, gesamt, wetter["temperatur"])

            # hoechste durchschnittliche Tageshoechsttemperatur
            avg_max = sum(tag["temperatur_max"] for tag in prognose) / len(prognose)
            if avg_max > max_temp:
                max_temp = avg_max
                waermste = (stadtname, round(avg_max, 1))

            # niedrigste durchschnittliche Tagestiefsttemperatur
            avg_min = sum(tag["temperatur_min"] for tag in prognose) / len(prognose)
            if avg_min < min_temp:
                min_temp = avg_min
                kaelteste = (stadtname, round(avg_min, 1))

        except RuntimeError:
            pass

    # Superlativ-Saetze ausgeben (nur, wenn ein Gewinner gefunden wurde)
    if sonnigste:
        st.success(f"☀️ Das sonnigste Wetter hat **{sonnigste[0]}** – aktuell {sonnigste[1]} °C.")
    if verregnetste:
        st.info(f"🌧️ Am meisten regnet es in **{verregnetste[0]}** – {round(verregnetste[1], 1)} mm Niederschlag, aktuell {verregnetste[2]} °C.")
    if waermste:
        st.warning(f"🥵 Am wärmsten ist es in **{waermste[0]}** – Ø Höchsttemperatur {waermste[1]} °C.")
    if kaelteste:
        st.info(f"🥶 Am kältesten ist es in **{kaelteste[0]}** – Ø Tiefsttemperatur {kaelteste[1]} °C.")
    st.divider()
    # ─────────────────────────────────────────
    # VERGLEICHSTABELLE (logik.staedte_vergleich)
    # Sortierte Uebersicht aller Staedte: Ø Temperaturen und Gesamtniederschlag
    # ─────────────────────────────────────────
    vergleich_df = logik.staedte_vergleich(vergleich_daten)
    if not vergleich_df.empty:
        st.markdown("#### 📊 Übersichtstabelle")
        st.dataframe(vergleich_df, use_container_width=True, hide_index=True)