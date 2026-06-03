"""
test_api_wetter.py -- Schnelltest: Open-Meteo-API erreichbar?
Dieses Skript ist nur fuer den ersten Verbindungstest (Variante B).
"""
import requests

URL = "https://api.open-meteo.com/v1/forecast"

STAEDTE = [
    {"name": "Leipzig",   "latitude": 51.34, "longitude": 12.37},
    {"name": "Dresden",   "latitude": 51.05, "longitude": 13.73},
    {"name": "Halle/Saale",    "latitude": 51.48, "longitude": 11.97},
    {"name": "Chemnitz",  "latitude": 50.83, "longitude": 12.92},
    {"name": "Döbeln",    "latitude": 51.11, "longitude": 13.08},
]

print("Verbinde mit Open-Meteo API...")

for stadt in STAEDTE:
    params = {
        "latitude":        stadt["latitude"],
        "longitude":       stadt["longitude"],
        "current_weather": True,
    }
    try:
        antwort = requests.get(URL, params=params, timeout=10)
        antwort.raise_for_status()
        daten = antwort.json()
        wetter = daten["current_weather"]

        print(f"\nAktuelles Wetter in {stadt['name']} (HTTP {antwort.status_code}):")
        print(f"  Temperatur:          {wetter['temperature']} Grad C")
        print(f"  Windgeschwindigkeit: {wetter['windspeed']} km/h")
        print(f"  Wettercode:          {wetter['weathercode']}")
        print(f"  Zeitpunkt:           {wetter['time']}")

    except requests.exceptions.ConnectionError:
        print(f"FEHLER ({stadt['name']}): Keine Internetverbindung.")
    except requests.exceptions.Timeout:
        print(f"FEHLER ({stadt['name']}): Zeitlimit ueberschritten (10 Sekunden).")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP-FEHLER ({stadt['name']}): {e}")
    except Exception as e:
        print(f"UNBEKANNTER FEHLER ({stadt['name']}): {e}")
