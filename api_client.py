"""
Modulname: api_client.py
Beschreibung: API-Aufruf und Datenaufbereitung
Autor: Anne-Katrin Dittmann
Datum: 2. Juni 2026
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_TIMEOUT = int(os.getenv("API_TIMEOUT", 10))

API_URL = "https://api.open-meteo.com/v1/forecast"


def wetter_aktuell_abrufen(breitengrad, laengengrad):
    """
    Ruft aktuelle Wetterdaten von Open-Meteo ab.
    
    Parameter:
        breitengrad (float): Breitengrad der Stadt
        laengengrad (float): Laengengrad der Stadt
    
    Rueckgabe:
        dict mit den Feldern:
            temperatur (float)
            windgeschwindigkeit (float)
            niederschlag (float) -- immer 0.0 bei current_weather
            wettercode (int)
        oder RuntimeError bei Fehler
    """
    params = {
        "latitude": breitengrad,
        "longitude": laengengrad,
        "current_weather": True,
        "hourly": "precipitation",
        "forecast_days": 1,
    }
    try:
        antwort = requests.get(API_URL, params=params,timeout=API_TIMEOUT)
        antwort.raise_for_status()
        daten = antwort.json()
        wetter = daten["current_weather"]
        return {
            "temperatur": wetter["temperature"],
            "windgeschwindigkeit": wetter["windspeed"],
            "niederschlag": 0.0,
            "wettercode": wetter["weathercode"],
        }
    except requests.exceptions.Timeout:
        raise RuntimeError("Wetter-API antwortet nicht (Timeout).")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Keine Internetverbindung.")
    except requests.exceptions.HTTPError as fehler:
        raise RuntimeError(f"API-Fehler: {fehler.response.status_code}")
    except (KeyError, ValueError):
        raise RuntimeError("Unerwartete Antwort der API.")


def prognose_abrufen(breitengrad, laengengrad, tage=7):
    """
    Ruft Prognosedaten fuer mehrere Tage von Open-Meteo ab.

    Parameter:
        breitengrad (float): Breitengrad der Stadt
        laengengrad (float): Laengengrad der Stadt
        tage (int): Anzahl der Prognosetage (Standard: 7)

    Rueckgabe:
        Liste von Dicts, je Tag ein Eintrag mit:
            datum (str)
            temperatur_min (float)
            temperatur_max (float)
            niederschlag (float)
            wettercode (int)
        oder RuntimeError bei Fehler
    """
    params = {
        "latitude": breitengrad,
        "longitude": laengengrad,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "forecast_days": tage,
        "timezone": "Europe/Berlin",
    }
    try:
        antwort = requests.get(API_URL, params=params, timeout=API_TIMEOUT)
        antwort.raise_for_status()
        daten = antwort.json()
        daily = daten["daily"]
        ergebnis = []
        for i in range(len(daily["time"])):
            ergebnis.append({
                "datum": daily["time"][i],
                "temperatur_min": daily["temperature_2m_min"][i],
                "temperatur_max": daily["temperature_2m_max"][i],
                "niederschlag": daily["precipitation_sum"][i],
                "wettercode": daily["weathercode"][i],
            })
        return ergebnis
    except requests.exceptions.Timeout:
        raise RuntimeError("Wetter-API antwortet nicht (Timeout).")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Keine Internetverbindung.")
    except requests.exceptions.HTTPError as fehler:
        raise RuntimeError(f"API-Fehler: {fehler.response.status_code}")
    except (KeyError, ValueError):
        raise RuntimeError("Unerwartete Antwort der API.")

def koordinaten_abrufen(stadtname, count=10):
    """
    Ruft Koordinaten fuer einen Stadtnamen ueber die Open-Meteo Geocoding API ab.
    Gibt bis zu 5 Treffer zurueck, damit der Nutzer bei Mehrdeutigkeit auswaehlen kann.

    Parameter:
        stadtname (str): Name der Stadt
        count (int): Anzahl der Treffer (Standard: 10)

    Rueckgabe:
        Liste von Dicts, je Treffer ein Eintrag mit:
            name (str)
            land (str)
            region (str)
            breitengrad (float)
            laengengrad (float)
        oder RuntimeError wenn Stadt nicht gefunden
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": stadtname,
        "count": count,
        "language": "de",
        "format": "json",
    }
    try:
        antwort = requests.get(url, params=params, timeout=API_TIMEOUT)
        antwort.raise_for_status()
        daten = antwort.json()
        if not daten.get("results"):
            raise RuntimeError(f"Stadt '{stadtname}' nicht gefunden.")
        treffer = []
        for ergebnis in daten["results"]:
            treffer.append({
                "name": ergebnis["name"],
                "land": ergebnis.get("country", ""),
                "region": ergebnis.get("admin1", ""),
                "breitengrad": ergebnis["latitude"],
                "laengengrad": ergebnis["longitude"],
            })
        return treffer
    except requests.exceptions.Timeout:
        raise RuntimeError("Geocoding-API antwortet nicht (Timeout).")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Keine Internetverbindung.")
    except requests.exceptions.HTTPError as fehler:
        raise RuntimeError(f"API-Fehler: {fehler.response.status_code}")
    
if __name__ == "__main__":
    print("Test: Aktuelles Wetter Leipzig")
    wetter = wetter_aktuell_abrufen(51.34, 12.37)
    print(wetter)
    print()
    print("Test: Prognose Leipzig (7 Tage)")
    prognose = prognose_abrufen(51.34, 12.37)
    for tag in prognose:
        print(tag)