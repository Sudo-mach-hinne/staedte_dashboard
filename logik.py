"""
Modulname: logik.py
Beschreibung: Berechnungen, pandas
Autor: Anne-Katrin Dittmann
Datum: 2. Juni 2026
"""
import pandas as pd

def stadt_einfuegen(name, land, lat, lon):
    """Speichert eine neue Stadt. Gibt die id der neuen oder bestehenden Zeile zurueck."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.execute(
            "INSERT OR IGNORE INTO staedte (name, land, breitengrad, laengengrad) "
            "VALUES (?, ?, ?, ?)",
            (name, land, lat, lon)
        )
        verbindung.commit()
        ergebnis = verbindung.execute(
            "SELECT id FROM staedte WHERE name = ?", (name,)
        ).fetchone()
        return ergebnis[0] if ergebnis else None

def durchschnittstemperatur(wetterdaten):
    """
    Berechnet die Durchschnittstemperatur aus gespeicherten Wetterdaten.

    Parameter:
        wetterdaten (list): Liste von Dicts aus datenbank.wetterdaten_nach_stadt()

    Rueckgabe:
        float -- Durchschnittstemperatur, oder None wenn keine Daten vorhanden
    """
    if not wetterdaten:
        return None
    df = pd.DataFrame(wetterdaten)
    return round(df["temperatur"].mean(), 2)


def temperatur_extremwerte(wetterdaten):
    """
    Berechnet Hoechst- und Tiefstwerte aus gespeicherten Wetterdaten.

    Parameter:
        wetterdaten (list): Liste von Dicts aus datenbank.wetterdaten_nach_stadt()

    Rueckgabe:
        dict mit minimum (float) und maximum (float), oder None wenn leer
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
        staedte_daten (list): Liste von Dicts mit den Feldern:
            name (str)
            prognose (list) -- Liste von Dicts aus datenbank.prognose_nach_stadt()

    Rueckgabe:
        pandas DataFrame mit einer Zeile pro Stadt.
        Sortiert nach Durchschnittstemperatur Max absteigend.
    """
    ergebnis = []
    for eintrag in staedte_daten:
        name = eintrag["name"]
        prognose = eintrag["prognose"]
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
    return pd.DataFrame(ergebnis).sort_values("Ø Temperatur Max (°C)", ascending=False)


def prognose_als_dataframe(prognose):
    """
    Wandelt eine Prognoseliste in einen sortierten pandas DataFrame um.

    Parameter:
        prognose (list): Liste von Dicts aus datenbank.prognose_nach_stadt()

    Rueckgabe:
        pandas DataFrame sortiert nach Datum
    """
    if not prognose:
        return pd.DataFrame()
    df = pd.DataFrame(prognose)
    df["datum"] = pd.to_datetime(df["datum"])
    return df.sort_values("datum").reset_index(drop=True)

def wettercode_zu_icon(wettercode):
    """Gibt einen Weather-Icons CSS-Klassennamen fuer einen WMO-Wettercode zurueck."""
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
        return "wi wi-na"

def wettercode_zu_icon(wettercode):
    """Gibt einen Weather-Icons CSS-Klassennamen fuer einen WMO-Wettercode zurueck."""
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
        return "wi wi-na"


if __name__ == "__main__":
    testdaten = [
        {"temperatur": 18.5, "windgeschwindigkeit": 12.3, "niederschlag": 0.0, "wettercode": 1},
        {"temperatur": 21.0, "windgeschwindigkeit": 8.0, "niederschlag": 0.2, "wettercode": 2},
        {"temperatur": 15.3, "windgeschwindigkeit": 20.1, "niederschlag": 1.5, "wettercode": 3},
    ]
    print("Durchschnittstemperatur:", durchschnittstemperatur(testdaten))
    print("Extremwerte:", temperatur_extremwerte(testdaten))