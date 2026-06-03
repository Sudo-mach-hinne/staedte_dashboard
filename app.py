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

# Seitenkonfiguration -- muss zuerst kommen!
st.set_page_config(page_title="City Weather Dashboard", layout="wide")

# Weather Icons Font einbinden
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.10/css/weather-icons.min.css">
""", unsafe_allow_html=True)

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

# Datenbank beim Start initialisieren
datenbank.initialisiere_datenbank()

st.title("🌍 City Weather Dashboard")

# Seitenleiste -- Navigation
seite = st.sidebar.radio(
    "Navigation",
    ["Wetter abrufen", "Meine Städte", "Städtevergleich"]
)

# ─────────────────────────────────────────────
# SEITE: Wetter abrufen
# ─────────────────────────────────────────────
if seite == "Wetter abrufen":
    st.header("Wetter abrufen")
    st.write("Gib eine Stadt ein und ruf das aktuelle Wetter sowie die Prognose für die nächsten 7 Tage ab. Die Stadt wird automatisch gespeichert.")

    stadtname = st.text_input("Stadt eingeben", placeholder="z. B. Leipzig")

    if st.button("Wetter abrufen"):
        if not stadtname.strip():
            st.error("Bitte einen Stadtnamen eingeben.")
        else:
            try:
                with st.spinner("Stadt wird gesucht..."):
                    geo = api_client.koordinaten_abrufen(stadtname.strip())

                datenbank.stadt_einfuegen(
                    geo["name"], geo["land"], geo["breitengrad"], geo["laengengrad"]
                )
                staedte = datenbank.alle_staedte()
                stadt = next(s for s in staedte if s["name"] == geo["name"])

                with st.spinner("Wetterdaten werden geladen..."):
                    wetter = api_client.wetter_aktuell_abrufen(
                        geo["breitengrad"], geo["laengengrad"]
                    )
                    prognose = api_client.prognose_abrufen(
                        geo["breitengrad"], geo["laengengrad"]
                    )

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

                # ── Aktuelles Wetter anzeigen ──
                st.divider()
                st.subheader(f"Aktuelles Wetter in {geo['name']}, {geo['land']}")

                icon_klasse = logik.wettercode_zu_icon(wetter["wettercode"])
                col_icon, col_temp, col_wind = st.columns([1, 2, 2])
                with col_icon:
                    st.markdown(
                        f'<i class="{icon_klasse}" style="font-size: 4rem; color: #f0a500;"></i>',
                        unsafe_allow_html=True
                    )
                with col_temp:
                    st.metric("Temperatur", f"{wetter['temperatur']} °C")
                with col_wind:
                    st.metric("Windgeschwindigkeit", f"{wetter['windgeschwindigkeit']} km/h")

                # Durchschnittstemperatur aus gespeicherten Daten
                wetterdaten_gespeichert = datenbank.wetterdaten_nach_stadt(stadt["id"])
                durchschnitt = logik.durchschnittstemperatur(wetterdaten_gespeichert)
                if durchschnitt:
                    st.info(f"Ø Temperatur aus allen bisherigen Abrufen: {durchschnitt} °C")

                # ── Prognose anzeigen ──
                st.divider()
                st.subheader("Prognose der nächsten 7 Tage")

                cols = st.columns(len(prognose))
                for i, tag in enumerate(prognose):
                    icon_klasse = logik.wettercode_zu_icon(tag["wettercode"])
                    with cols[i]:
                        st.markdown(f"**{tag['datum']}**")
                        st.markdown(
                            f'<i class="{icon_klasse}" style="font-size: 2rem; color: #f0a500;"></i>',
                            unsafe_allow_html=True
                        )
                        st.write(f"↑ {tag['temperatur_max']} °C")
                        st.write(f"↓ {tag['temperatur_min']} °C")
                        st.write(f"🌧 {tag['niederschlag']} mm")

            except RuntimeError as fehler:
                st.error(str(fehler))

# ─────────────────────────────────────────────
# SEITE: Meine Städte
# ─────────────────────────────────────────────
elif seite == "Meine Städte":
    st.header("Meine Städte")
    st.write("Hier siehst du alle Städte, deren Wetter du bereits abgerufen hast. Du kannst Städte aus der Liste entfernen.")

    staedte = datenbank.alle_staedte()

    if not staedte:
        st.info("Noch keine Städte gespeichert. Geh auf 'Wetter abrufen' und suche eine Stadt.")
    else:
        for stadt in staedte:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(
                    f"**{stadt['name']}** — {stadt['land']} "
                    f"| Breitengrad: {stadt['breitengrad']} "
                    f"| Längengrad: {stadt['laengengrad']} "
                    f"| Gespeichert am: {stadt['angelegt_am']}"
                )
            with col2:
                if st.button("🗑️ Entfernen", key=f"loeschen_{stadt['id']}"):
                    datenbank.stadt_loeschen(stadt["id"])
                    st.success(f"{stadt['name']} wurde entfernt.")
                    st.rerun()

# ─────────────────────────────────────────────
# SEITE: Städtevergleich
# ─────────────────────────────────────────────
elif seite == "Städtevergleich":
    st.header("Städtevergleich")
    st.write("Vergleiche das Wetter mehrerer Städte anhand der gespeicherten Prognosedaten.")

    staedte = datenbank.alle_staedte()

    if not staedte:
        st.info("Noch keine Städte gespeichert. Geh auf 'Wetter abrufen' und suche eine Stadt.")
    else:
        auswahl = st.multiselect(
            "Städte auswählen",
            options=[s["name"] for s in staedte],
            default=[s["name"] for s in staedte[:2]]
        )

        if len(auswahl) < 2:
            st.warning("Bitte mindestens zwei Städte auswählen.")
        else:
            if st.button("Vergleich starten"):
                staedte_daten = []
                for name in auswahl:
                    stadt = next(s for s in staedte if s["name"] == name)
                    prognose = datenbank.prognose_nach_stadt(stadt["id"])
                    staedte_daten.append({"name": name, "prognose": prognose})

                vergleich_df = logik.staedte_vergleich(staedte_daten)

                if vergleich_df.empty:
                    st.warning("Keine Prognosedaten vorhanden. Bitte zuerst Wetter abrufen.")
                else:
                    st.subheader("Vergleichsübersicht")
                    st.dataframe(vergleich_df, width="stretch")

                    beste_stadt = vergleich_df.iloc[0]["name"]
                    st.success(f"🌞 Wärmste Stadt in den nächsten Tagen: {beste_stadt}")