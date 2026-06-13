"""
Modulname: api_client.py
Beschreibung: API-Aufruf und Datenaufbereitung
Autor: Anne-Katrin Dittmann
Datum: 2. Juni 2026
"""

import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

API_TIMEOUT = int(os.getenv("API_TIMEOUT", 10))

# API-Endpunkte
API_URL        = "https://api.open-meteo.com/v1/forecast"
FALLBACK_URL   = "https://wttr.in"
LAENDER_URL    = "https://restcountries.com/v3.1/name"
HISTORISCH_URL = "https://archive-api.open-meteo.com/v1/archive"
KLIMA_URL      = "https://climate-api.open-meteo.com/v1/climate"


def _wetter_fallback_aktuell(stadtname):
    """
    Fallback: Ruft aktuelle Wetterdaten von wttr.in ab.

    Parameter:
        stadtname (str): Name der Stadt

    Rueckgabe:
        dict mit den Feldern:
            temperatur (float)
            windgeschwindigkeit (float)
            niederschlag (float)
            wettercode (int)
        oder RuntimeError bei Fehler
    """
    url = f"{FALLBACK_URL}/{stadtname}?format=j1"
    antwort = requests.get(url, timeout=API_TIMEOUT)
    antwort.raise_for_status()
    daten = antwort.json()
    aktuell = daten["current_condition"][0]
    return {
        "temperatur": float(aktuell["temp_C"]),
        "windgeschwindigkeit": float(aktuell["windspeedKmph"]),
        "niederschlag": float(aktuell["precipMM"]),
        "wettercode": int(aktuell["weatherCode"]),
    }


def _wetter_fallback_prognose(stadtname, tage=7):
    """
    Fallback: Ruft Prognosedaten von wttr.in ab.

    Parameter:
        stadtname (str): Name der Stadt
        tage (int): Anzahl der Tage (wttr.in liefert max. 3)

    Rueckgabe:
        Liste von Dicts je Tag mit:
            datum (str)
            temperatur_min (float)
            temperatur_max (float)
            niederschlag (float)
            wettercode (int)
        oder RuntimeError bei Fehler
    """
    url = f"{FALLBACK_URL}/{stadtname}?format=j1"
    antwort = requests.get(url, timeout=API_TIMEOUT)
    antwort.raise_for_status()
    daten = antwort.json()
    ergebnis = []
    for tag in daten["weather"][:tage]:
        ergebnis.append({
            "datum": tag["date"],
            "temperatur_min": float(tag["mintempC"]),
            "temperatur_max": float(tag["maxtempC"]),
            "niederschlag": float(tag["hourly"][0]["precipMM"]),
            "wettercode": int(tag["hourly"][0]["weatherCode"]),
        })
    return ergebnis


def wetter_aktuell_abrufen(breitengrad, laengengrad, stadtname=None):
    """
    Ruft aktuelle Wetterdaten von Open-Meteo ab.
    Bei Fehler: Fallback auf wttr.in (erfordert stadtname).

    Parameter:
        breitengrad (float): Breitengrad der Stadt
        laengengrad (float): Laengengrad der Stadt
        stadtname (str): Name der Stadt (fuer Fallback benoetigt)

    Rueckgabe:
        dict mit den Feldern:
            temperatur (float)
            windgeschwindigkeit (float)
            niederschlag (float)
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
        antwort = requests.get(API_URL, params=params, timeout=API_TIMEOUT)
        antwort.raise_for_status()
        daten = antwort.json()
        wetter = daten["current_weather"]
        return {
            "temperatur": wetter["temperature"],
            "windgeschwindigkeit": wetter["windspeed"],
            "niederschlag": 0.0,
            "wettercode": wetter["weathercode"],
        }
    except Exception:
        if stadtname:
            try:
                return _wetter_fallback_aktuell(stadtname)
            except Exception as fallback_fehler:
                raise RuntimeError(
                    f"Beide APIs nicht erreichbar. Fallback-Fehler: {fallback_fehler}"
                )
        raise RuntimeError("Wetter-API nicht erreichbar und kein Stadtname fuer Fallback angegeben.")


def prognose_abrufen(breitengrad, laengengrad, tage=7, stadtname=None):
    """
    Ruft Prognosedaten fuer mehrere Tage von Open-Meteo ab.
    Bei Fehler: Fallback auf wttr.in (max. 3 Tage, erfordert stadtname).

    Parameter:
        breitengrad (float): Breitengrad der Stadt
        laengengrad (float): Laengengrad der Stadt
        tage (int): Anzahl der Prognosetage (Standard: 7)
        stadtname (str): Name der Stadt (fuer Fallback benoetigt)

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
    except Exception:
        if stadtname:
            try:
                return _wetter_fallback_prognose(stadtname, tage)
            except Exception as fallback_fehler:
                raise RuntimeError(
                    f"Beide APIs nicht erreichbar. Fallback-Fehler: {fallback_fehler}"
                )
        raise RuntimeError("Prognose-API nicht erreichbar und kein Stadtname fuer Fallback angegeben.")


def koordinaten_abrufen(stadtname, count=10):
    """
    Ruft Koordinaten fuer einen Stadtnamen ueber die Open-Meteo Geocoding API ab.
    Gibt bis zu 10 Treffer zurueck, damit der Nutzer bei Mehrdeutigkeit auswaehlen kann.

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
                "kreis": ergebnis.get("admin2", ""),
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


def laenderdaten_abrufen(landname):
    """
    Ruft Laenderfakten von REST Countries ab.

    Parameter:
        landname (str): Name des Landes (z. B. "Germany")

    Rueckgabe:
        dict mit den Feldern:
            hauptstadt (str)
            waehrung (str)
            sprachen (str)
        oder None bei Fehler
    """
    try:
        url = f"{LAENDER_URL}/{landname}"
        antwort = requests.get(url, timeout=API_TIMEOUT)
        antwort.raise_for_status()
        daten = antwort.json()[0]

        # Hauptstadt
        hauptstadt = daten.get("capital", ["unbekannt"])[0]

        # Waehrung -- Datenstruktur: {"EUR": {"name": "Euro", "symbol": "€"}}
        waehrungen = daten.get("currencies", {})
        waehrung = ", ".join(
            f"{v.get('name', k)} ({v.get('symbol', '')})"
            for k, v in waehrungen.items()
        )

        # Sprachen -- Datenstruktur: {"deu": "German"}
        sprachen_dict = daten.get("languages", {})
        sprachen = ", ".join(sprachen_dict.values())

        return {
            "hauptstadt": hauptstadt,
            "waehrung": waehrung,
            "sprachen": sprachen,
        }
    except Exception:
        return None


def historisches_wetter_abrufen(breitengrad, laengengrad, datum_von, datum_bis):
    """
    Ruft historische Wetterdaten von der Open-Meteo Archive API ab.

    Parameter:
        breitengrad (float): Breitengrad der Stadt
        laengengrad (float): Laengengrad der Stadt
        datum_von (str): Startdatum im Format YYYY-MM-DD
        datum_bis (str): Enddatum im Format YYYY-MM-DD

    Rueckgabe:
        Liste von Dicts je Tag mit:
            datum (str)
            temperatur_max (float)
            temperatur_min (float)
            niederschlag (float)
        oder RuntimeError bei Fehler
    """
    params = {
        "latitude": breitengrad,
        "longitude": laengengrad,
        "start_date": datum_von,
        "end_date": datum_bis,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Europe/Berlin",
    }
    try:
        antwort = requests.get(HISTORISCH_URL, params=params, timeout=API_TIMEOUT)
        antwort.raise_for_status()
        daten = antwort.json()
        daily = daten["daily"]
        ergebnis = []
        for i in range(len(daily["time"])):
            ergebnis.append({
                "datum": daily["time"][i],
                "temperatur_max": daily["temperature_2m_max"][i],
                "temperatur_min": daily["temperature_2m_min"][i],
                "niederschlag": daily["precipitation_sum"][i] or 0.0,
            })
        return ergebnis
    except Exception as fehler:
        raise RuntimeError(f"Historische Wetter-API nicht erreichbar: {fehler}")


def reisewetter_abrufen(breitengrad, laengengrad):
    """
    Ruft klimatologische Monatsdurchschnitte von der Open-Meteo Climate API ab.
    Liefert eine Jahresuebersicht mit Durchschnittstemperaturen und Niederschlag.

    Parameter:
        breitengrad (float): Breitengrad der Stadt
        laengengrad (float): Laengengrad der Stadt

    Rueckgabe:
        Liste von 12 Dicts (Januar bis Dezember) mit:
            monat (str)
            temperatur_max (float)
            temperatur_min (float)
            niederschlag (float)
        oder RuntimeError bei Fehler
    """
    params = {
        "latitude": breitengrad,
        "longitude": laengengrad,
        "start_date": "1991-01-01",
        "end_date": "2020-12-31",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Europe/Berlin",
        "models": "EC_Earth3P_HR",
    }
    try:
        antwort = requests.get(KLIMA_URL, params=params, timeout=30)
        antwort.raise_for_status()
        daten = antwort.json()
        daily = daten["daily"]

        df = pd.DataFrame({
            "datum": pd.to_datetime(daily["time"]),
            "temperatur_max": daily["temperature_2m_max"],
            "temperatur_min": daily["temperature_2m_min"],
            "niederschlag": [x or 0.0 for x in daily["precipitation_sum"]],
        })
        df["monat"] = df["datum"].dt.month

        monate_namen = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                        "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
        ergebnis = []
        for m in range(1, 13):
            monats_df = df[df["monat"] == m]
            ergebnis.append({
                "monat": monate_namen[m - 1],
                "temperatur_max": round(monats_df["temperatur_max"].mean(), 1),
                "temperatur_min": round(monats_df["temperatur_min"].mean(), 1),
                "niederschlag": round(monats_df["niederschlag"].mean(), 1),
            })
        return ergebnis
    except Exception as fehler:
        raise RuntimeError(f"Reisewetter-API nicht erreichbar: {fehler}")


# ---------------------------------------------------------------------------
# Manuelle Testausgabe (nur bei direktem Aufruf, nicht beim Import)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Test: Aktuelles Wetter Leipzig")
    wetter = wetter_aktuell_abrufen(51.34, 12.37, stadtname="Leipzig")
    print(wetter)
    print()
    print("Test: Prognose Leipzig (7 Tage)")
    prognose = prognose_abrufen(51.34, 12.37, tage=7, stadtname="Leipzig")
    for tag in prognose:
        print(tag)
    print()
    print("Test: Laenderdaten Deutschland")
    laender = laenderdaten_abrufen("Germany")
    print(laender)