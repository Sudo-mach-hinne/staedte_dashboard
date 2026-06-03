"""
Modulname: logik.py
Beschreibung: Berechnungen, pandas
Autor: Anne-Katrin Dittmann
Datum: 2. Juni 2026
"""
import pandas as pd
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
        pandas DataFrame mit einer Zeile pro Stadt und den Spalten:
            name, durchschnitt_max, durchschnitt_min, gesamtniederschlag
        Sortiert nach durchschnitt_max absteigend.
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
            "durchschnitt_max": round(df["temperatur_max"].mean(), 2),
            "durchschnitt_min": round(df["temperatur_min"].mean(), 2),
            "gesamtniederschlag": round(df["niederschlag"].sum(), 2),
        })
    if not ergebnis:
        return pd.DataFrame()
    return pd.DataFrame(ergebnis).sort_values("durchschnitt_max", ascending=False)


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


if __name__ == "__main__":
    # Testdaten
    testdaten = [
        {"temperatur": 18.5, "windgeschwindigkeit": 12.3, "niederschlag": 0.0, "wettercode": 1},
        {"temperatur": 21.0, "windgeschwindigkeit": 8.0, "niederschlag": 0.2, "wettercode": 2},
        {"temperatur": 15.3, "windgeschwindigkeit": 20.1, "niederschlag": 1.5, "wettercode": 3},
    ]
    print("Durchschnittstemperatur:", durchschnittstemperatur(testdaten))
    print("Extremwerte:", temperatur_extremwerte(testdaten))

    testprognose_leipzig = [
        {"datum": "2026-06-04", "temperatur_min": 14.0, "temperatur_max": 22.0, "niederschlag": 0.5, "wettercode": 2},
        {"datum": "2026-06-05", "temperatur_min": 13.0, "temperatur_max": 20.0, "niederschlag": 1.0, "wettercode": 3},
    ]
    testprognose_berlin = [
        {"datum": "2026-06-04", "temperatur_min": 12.0, "temperatur_max": 19.0, "niederschlag": 2.0, "wettercode": 3},
        {"datum": "2026-06-05", "temperatur_min": 11.0, "temperatur_max": 18.0, "niederschlag": 0.0, "wettercode": 1},
    ]
    vergleich = staedte_vergleich([
        {"name": "Leipzig", "prognose": testprognose_leipzig},
        {"name": "Berlin", "prognose": testprognose_berlin},
    ])
    print()
    print("Staedtevergleich:")
    print(vergleich)