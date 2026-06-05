"""
Modulname: logik.py
Beschreibung: Berechnungen und Auswertungen mit pandas.
              Kein Datenbankzugriff, keine API-Aufrufe — nur reine Logik.
Autor: Anne-Katrin Dittmann
Datum: 2. Juni 2026
"""

import pandas as pd


def durchschnittstemperatur(wetterdaten):
    """
    Berechnet die Durchschnittstemperatur aus gespeicherten Wetterdaten.

    Parameter:
        wetterdaten (list): Liste von Dicts aus datenbank.wetterdaten_nach_stadt().
                            Jeder Dict muss das Feld 'temperatur' (float) enthalten.

    Rueckgabe:
        float -- Durchschnittstemperatur gerundet auf 2 Nachkommastellen,
                 oder None wenn die Liste leer ist.
    """
    if not wetterdaten:
        return None

    df = pd.DataFrame(wetterdaten)
    return round(df["temperatur"].mean(), 2)


def temperatur_extremwerte(wetterdaten):
    """
    Berechnet Hoechst- und Tiefstwerte aus gespeicherten Wetterdaten.

    Parameter:
        wetterdaten (list): Liste von Dicts aus datenbank.wetterdaten_nach_stadt().
                            Jeder Dict muss das Feld 'temperatur' (float) enthalten.

    Rueckgabe:
        dict mit den Schlüsseln:
            'minimum' (float) -- niedrigste gemessene Temperatur
            'maximum' (float) -- hoechste gemessene Temperatur
        oder None wenn die Liste leer ist.
    """
    if not wetterdaten:
        return None

    df = pd.DataFrame(wetterdaten)
    return {
        "minimum": round(df["temperatur"].min(), 2),
        "maximum": round(df["temperatur"].max(), 2),
    }


def staedte_vergleich(staedte_daten):
    """
    Vergleicht mehrere Staedte anhand ihrer Prognosedaten.

    Parameter:
        staedte_daten (list): Liste von Dicts, jeweils mit:
            'name'     (str)  -- Stadtname
            'prognose' (list) -- Prognosedaten aus datenbank.prognose_nach_stadt()

    Rueckgabe:
        pandas DataFrame mit einer Zeile pro Stadt, sortiert nach
        Durchschnittstemperatur Max absteigend.
        Leerer DataFrame wenn keine Daten vorhanden.
    """
    ergebnis = []

    for eintrag in staedte_daten:
        name = eintrag["name"]
        prognose = eintrag["prognose"]

        # Staedte ohne Prognosedaten werden uebersprungen
        if not prognose:
            continue

        df = pd.DataFrame(prognose)

        ergebnis.append({
            "name": name,
            "Ø Temperatur Max (°C)": round(df["temperatur_max"].mean(), 2),
            "Ø Temperatur Min (°C)": round(df["temperatur_min"].mean(), 2),
            "Gesamtniederschlag (mm)": round(df["niederschlag"].sum(), 2),
        })

    if not ergebnis:
        return pd.DataFrame()

    # Ergebnis nach Hoechsttemperatur absteigend sortieren
    return pd.DataFrame(ergebnis).sort_values("Ø Temperatur Max (°C)", ascending=False)


def prognose_als_dataframe(prognose):
    """
    Wandelt eine Prognoseliste in einen sortierten pandas DataFrame um.

    Parameter:
        prognose (list): Liste von Dicts aus datenbank.prognose_nach_stadt().

    Rueckgabe:
        pandas DataFrame sortiert nach Datum (aufsteigend),
        oder leerer DataFrame wenn keine Daten vorhanden.
    """
    if not prognose:
        return pd.DataFrame()

    df = pd.DataFrame(prognose)

    # Datum als echten datetime-Typ umwandeln fuer korrekte Sortierung
    df["datum"] = pd.to_datetime(df["datum"])

    return df.sort_values("datum").reset_index(drop=True)


def wettercode_zu_icon(wettercode):
    """
    Gibt einen Weather-Icons CSS-Klassennamen fuer einen WMO-Wettercode zurueck.

    WMO-Wettercodes (Auswahl):
        0        -- Klarer Himmel
        1, 2     -- Ueberwiegend klar / teilweise bewoelkt
        3        -- Bedeckt
        51-67    -- Nieselregen / Regen
        71-77    -- Schneefall
        80-82    -- Regenschauer
        95-99    -- Gewitter

    Parameter:
        wettercode (int): WMO-Wettercode aus der Open-Meteo API.

    Rueckgabe:
        str -- CSS-Klassenname fuer die Weather-Icons Bibliothek.
               'wi wi-na' fuer unbekannte Codes.
    """
    if wettercode == 0:
        return "wi wi-day-sunny"
    elif wettercode in [1, 2]:
        return "wi wi-day-cloudy"
    elif wettercode == 3:
        return "wi wi-cloudy"
    elif wettercode in range(51, 68):
        return "wi wi-rain"
    elif wettercode in range(71, 78):
        return "wi wi-snow"
    elif wettercode in range(80, 83):
        return "wi wi-showers"
    elif wettercode in range(95, 100):
        return "wi wi-thunderstorm"
    else:
        # Unbekannter oder nicht unterstuetzter Wettercode
        return "wi wi-na"


# ---------------------------------------------------------------------------
# Manuelle Testausgabe (nur bei direktem Aufruf, nicht beim Import)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    testdaten = [
        {"temperatur": 18.5, "windgeschwindigkeit": 12.3, "niederschlag": 0.0, "wettercode": 1},
        {"temperatur": 21.0, "windgeschwindigkeit": 8.0,  "niederschlag": 0.2, "wettercode": 2},
        {"temperatur": 15.3, "windgeschwindigkeit": 20.1, "niederschlag": 1.5, "wettercode": 3},
    ]
    print("Durchschnittstemperatur:", durchschnittstemperatur(testdaten))
    print("Extremwerte:", temperatur_extremwerte(testdaten))