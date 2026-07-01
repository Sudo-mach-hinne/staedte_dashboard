"""
Modulname: datenbank.py
Beschreibung: Alle SQLite-Datenbankoperationen fuer das City Weather Dashboard.
Kein API-Zugriff und keine Berechnungen. 
Nur Datenzugriff.

Autor: Anne-Katrin Dittmann
Datum: 2. Juni 2026
"""

import os
import sqlite3
from contextlib import closing

from dotenv import load_dotenv

# Umgebungsvariablen aus .env laden (z. B. DB_PFAD)
load_dotenv()

# Datenbankpfad aus .env lesen, Standardwert falls nicht gesetzt
DB_PFAD = os.getenv("DB_PFAD", "daten/projekt.db")

# Verzeichnis anlegen falls noch nicht vorhanden
os.makedirs("daten", exist_ok=True)


def initialisiere_datenbank():
    """
    Legt alle Tabellen an, falls sie noch nicht existieren.
    Wird beim Start der Anwendung einmalig aufgerufen.

    Tabellen:
        staedte: Verwaltung der gespeicherten Städte
        wetterdaten: Verlauf der abgerufenen aktuellen Wetterdaten
        prognose: Gespeicherte 7-Tage-Prognosedaten
    """
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        # Tabelle: Staedte
        verbindung.execute("""
            CREATE TABLE IF NOT EXISTS staedte (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                land        TEXT,
                region      TEXT,
                breitengrad REAL,
                laengengrad REAL,
                angelegt_am TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (breitengrad, laengengrad)
            )
        """)

        # Tabelle: Aktuelle Wetterdaten (Verlauf)
        verbindung.execute("""
            CREATE TABLE IF NOT EXISTS wetterdaten (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                stadt_id            INTEGER NOT NULL,
                abgerufen_am        TEXT DEFAULT CURRENT_TIMESTAMP,
                temperatur          REAL,
                windgeschwindigkeit REAL,
                niederschlag        REAL,
                wettercode          INTEGER,
                FOREIGN KEY (stadt_id) REFERENCES staedte(id)
            )
        """)

        # Tabelle: 7-Tage-Prognosedaten
        verbindung.execute("""
            CREATE TABLE IF NOT EXISTS prognose (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                stadt_id        INTEGER NOT NULL,
                datum           TEXT NOT NULL,
                temperatur_min  REAL,
                temperatur_max  REAL,
                niederschlag    REAL,
                wettercode      INTEGER,
                FOREIGN KEY (stadt_id) REFERENCES staedte(id)
            )
        """)

        # ─────────────────────────────────────────────
        # SCHEMA-MIGRATION
        # CREATE TABLE IF NOT EXISTS aendert eine bereits bestehende Tabelle
        # NICHT. Aeltere Datenbanken haben die Spalte 'region' noch nicht.
        # Deshalb hier pruefen und bei Bedarf per ALTER TABLE nachruesten --
        # so muss keine Datenbank geloescht werden und es gehen keine Daten
        # verloren.
        # ─────────────────────────────────────────────
        vorhandene_spalten = [
            spalte[1] for spalte in verbindung.execute("PRAGMA table_info(staedte)")
        ]
        if "region" not in vorhandene_spalten:
            verbindung.execute("ALTER TABLE staedte ADD COLUMN region TEXT")

        verbindung.commit()


def stadt_einfuegen(name, land, lat, lon, region=""):
    """
    Speichert eine neue Stadt in der Datenbank.
    Bereits vorhandene Städte (gleiche Koordinaten) werden ignoriert
    (INSERT OR IGNORE).

    Parameter:
        name (str): Stadtname
        land (str): Landesname
        lat (float): Breitengrad
        lon (float): Längengrad
        region (str): Bundesland/Region (optional, zur besseren
            geografischen Abgrenzung gleichnamiger Orte)

    Rückgabe:
        int: ID der Stadt. Bei einer neuen Stadt die neu vergebene ID,
            bei einer bereits vorhandenen Stadt (gleiche Koordinaten)
            die ID des bestehenden Eintrags. So bekommt der Aufrufer
            immer eine gültige ID zurück.
    """
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        # Neue Stadt anlegen. Existiert die Koordinate schon, passiert nichts
        # (INSERT OR IGNORE greift wegen UNIQUE auf breitengrad/laengengrad).
        verbindung.execute(
            "INSERT OR IGNORE INTO staedte (name, land, region, breitengrad, laengengrad) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, land, region, lat, lon)
        )
        # Region auch bei bereits vorhandenen Staedten nachtragen, falls sie
        # dort noch fehlt (z. B. Eintraege aus einer aelteren Datenbankversion).
        if region:
            verbindung.execute(
                "UPDATE staedte SET region = ? "
                "WHERE breitengrad = ? AND laengengrad = ? "
                "AND (region IS NULL OR region = '')",
                (region, lat, lon)
            )
        verbindung.commit()

        # ID ueber die Koordinaten holen -- funktioniert sowohl fuer die eben
        # eingefuegte als auch fuer eine bereits vorhandene Stadt.
        zeile = verbindung.execute(
            "SELECT id FROM staedte WHERE breitengrad = ? AND laengengrad = ?",
            (lat, lon)
        ).fetchone()
        return zeile[0] if zeile else None


def stadt_loeschen(stadt_id):
    """
    Löscht eine Stadt sowie alle zugehörigen Wetter- und Prognosedaten.

    Parameter:
        stadt_id (int): ID der zu löschenden Stadt
    """
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        # Zuerst abhaengige Datensaetze loeschen, dann die Stadt selbst
        verbindung.execute("DELETE FROM wetterdaten WHERE stadt_id = ?", (stadt_id,))
        verbindung.execute("DELETE FROM prognose WHERE stadt_id = ?", (stadt_id,))
        verbindung.execute("DELETE FROM staedte WHERE id = ?", (stadt_id,))
        verbindung.commit()


def alle_staedte():
    """
    Liefert alle gespeicherten Städte.

    Rückgabe:
        list: Liste von Dicts, je ein Dict pro Stadt
    """
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.row_factory = sqlite3.Row
        return [dict(zeile) for zeile in
                verbindung.execute("SELECT * FROM staedte")]


def stadt_nach_id(stadt_id):
    """
    Liefert eine einzelne Stadt anhand ihrer ID.

    Parameter:
        stadt_id (int): ID der gesuchten Stadt

    Rückgabe:
        dict oder None: Stadtdaten, oder None wenn nicht gefunden
    """
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.row_factory = sqlite3.Row
        ergebnis = verbindung.execute(
            "SELECT * FROM staedte WHERE id = ?", (stadt_id,)
        ).fetchone()
        return dict(ergebnis) if ergebnis else None


def wetterdaten_speichern(stadt_id, temperatur, windgeschwindigkeit, niederschlag, wettercode):
    """
    Speichert einen aktuellen Wetterdatensatz für eine Stadt.
    Jeder Aufruf erzeugt einen neuen Eintrag mit aktuellem Zeitstempel.

    Parameter:
        stadt_id (int): ID der Stadt
        temperatur (float): Aktuelle Temperatur in °C
        windgeschwindigkeit (float): Windgeschwindigkeit in km/h
        niederschlag (float): Niederschlag in mm
        wettercode (int): WMO-Wettercode
    """
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.execute(
            "INSERT INTO wetterdaten "
            "(stadt_id, temperatur, windgeschwindigkeit, niederschlag, wettercode) "
            "VALUES (?, ?, ?, ?, ?)",
            (stadt_id, temperatur, windgeschwindigkeit, niederschlag, wettercode)
        )
        verbindung.commit()


def wetterdaten_nach_stadt(stadt_id):
    """
    Liefert alle gespeicherten Wetterdaten einer Stadt, neueste zuerst.

    Parameter:
        stadt_id (int): ID der Stadt

    Rückgabe:
        list: Liste von Dicts, je ein Dict pro Wetterdatensatz
    """
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.row_factory = sqlite3.Row
        return [dict(zeile) for zeile in
                verbindung.execute(
                    "SELECT * FROM wetterdaten WHERE stadt_id = ? ORDER BY abgerufen_am DESC",
                    (stadt_id,)
                )]


def prognose_speichern(stadt_id, datum, temp_min, temp_max, niederschlag, wettercode):
    """
    Speichert einen Prognosedatensatz für eine Stadt und ein Datum.

    Parameter:
        stadt_id (int): ID der Stadt
        datum (str): Prognosedatum im Format YYYY-MM-DD
        temp_min (float): Tagestiefsttemperatur in °C
        temp_max (float): Tageshöchsttemperatur in °C
        niederschlag (float): Niederschlagssumme in mm
        wettercode (int): WMO-Wettercode
    """
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.execute(
            "INSERT INTO prognose "
            "(stadt_id, datum, temperatur_min, temperatur_max, niederschlag, wettercode) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (stadt_id, datum, temp_min, temp_max, niederschlag, wettercode)
        )
        verbindung.commit()


def prognose_nach_stadt(stadt_id):
    """
    Liefert alle gespeicherten Prognosedaten einer Stadt, chronologisch sortiert.

    Parameter:
        stadt_id (int): ID der Stadt

    Rückgabe:
        list: Liste von Dicts, je ein Dict pro Prognosetag
    """
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.row_factory = sqlite3.Row
        return [dict(zeile) for zeile in
                verbindung.execute(
                    "SELECT * FROM prognose WHERE stadt_id = ? ORDER BY datum ASC",
                    (stadt_id,)
                )]


# ---------------------------------------------------------------------------
# Manuelle Testausgabe (nur bei direktem Aufruf, nicht beim Import)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    initialisiere_datenbank()
    print("Datenbank initialisiert.")

    id1 = stadt_einfuegen("Leipzig", "Deutschland", 51.34, 12.37)
    id2 = stadt_einfuegen("Berlin", "Deutschland", 52.52, 13.40)
    print("Staedte eingefuegt:", alle_staedte())

    wetterdaten_speichern(id1, 18.5, 12.3, 0.0, 1)
    prognose_speichern(id1, "2026-06-04", 14.0, 22.0, 0.5, 2)
    print("Wetterdaten Leipzig:", wetterdaten_nach_stadt(id1))
    print("Prognose Leipzig:", prognose_nach_stadt(id1))