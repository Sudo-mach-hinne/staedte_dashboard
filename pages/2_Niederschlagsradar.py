import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Niederschlagsradar", layout="wide")
st.title("Niederschlagsradar")

RAINVIEWER_API = "https://api.rainviewer.com/public/weather-maps.json"


def radar_zeitpunkte_abrufen():
    """Holt die verfügbaren Radar-Zeitpunkte von RainViewer."""
    try:
        antwort = requests.get(RAINVIEWER_API, timeout=5)
        antwort.raise_for_status()
        return antwort.json()
    except requests.exceptions.RequestException:
        raise RuntimeError("Radar-Daten konnten nicht geladen werden.")


breite = st.number_input("Breitengrad", value=51.34, format="%.4f")
laenge = st.number_input("Längengrad", value=12.37, format="%.4f")

try:
    daten = radar_zeitpunkte_abrufen()
    host = daten["host"]
    # letztes (aktuellstes) Radarbild nehmen
    letzter_frame = daten["radar"]["past"][-1]
    pfad = letzter_frame["path"]

    # Karte zentriert auf die Koordinaten
    karte = folium.Map(location=[breite, laenge], zoom_start=7)

    # Radar-Kacheln als Overlay
    # {z}/{x}/{y} füllt folium automatisch; 256=Auflösung, 2=Farbschema, 1_1=glättung+Schatten
    tile_url = f"{host}{pfad}/256/{{z}}/{{x}}/{{y}}/2/1_1.png"
    folium.TileLayer(
        tiles=tile_url,
        attr="RainViewer",
        name="Niederschlag",
        opacity=0.6,
    ).add_to(karte)

    st_folium(karte, width=900, height=500)
    st.caption("Radardaten: RainViewer")

except RuntimeError as fehler:
    st.error(str(fehler))