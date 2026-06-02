"""
test_api_wetter.py -- Schnelltest: Open-Meteo-API erreichbar?
Dieses Skript ist nur fuer den ersten Verbindungstest (Variante B).
"""
import requests

URL = "https://api.open-meteo.com/v1/forecast"

# Berlin als Testkoordinaten
PARAMS = {
    "latitude": 52.52,
    "longitude": 13.41,
    "current_weather": True,
}

print("Verbinde mit Open-Meteo API...")

try:
    antwort = requests.get(URL, params=PARAMS, timeout=10)
    antwort.raise_for_status()
    daten = antwort.json()

    print(f"Verbindung erfolgreich! HTTP-Status: {antwort.status_code}")
    print()
    wetter = daten["current_weather"]
    print("Aktuelles Wetter in Berlin:")
    print(f"  Temperatur:        {wetter['temperature']} Grad C")
    print(f"  Windgeschwindigkeit: {wetter['windspeed']} km/h")
    print(f"  Wettercode:        {wetter['weathercode']}")
    print(f"  Zeitpunkt:         {wetter['time']}")

except requests.exceptions.ConnectionError:
    print("FEHLER: Keine Internetverbindung.")
except requests.exceptions.Timeout:
    print("FEHLER: Zeitlimit ueberschritten (10 Sekunden).")
except requests.exceptions.HTTPError as e:
    print(f"HTTP-FEHLER: {e}")
except Exception as e:
    print(f"UNBEKANNTER FEHLER: {e}")