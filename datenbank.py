"""
Modulname: datenbank.py
Beschreibung: SQLite-Zugriff
Autor: Anne-Katrin Dittmann
Datum: 2. Juni 2026
"""

import sqlite3
from contextlib import closing

import os
from dotenv import load_dotenv

load_dotenv()

DB_PFAD = os.getenv("DB_PFAD", "daten/projekt.db")


def initialisiere_datenbank():
    """Legt alle Tabellen an, falls sie noch nicht existieren."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.execute("""
            CREATE TABLE IF NOT EXISTS staedte (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                land TEXT,
                breitengrad REAL,
                laengengrad REAL,
                angelegt_am TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        verbindung.execute("""
            CREATE TABLE IF NOT EXISTS wetterdaten (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stadt_id INTEGER NOT NULL,
                abgerufen_am TEXT DEFAULT CURRENT_TIMESTAMP,
                temperatur REAL,
                windgeschwindigkeit REAL,
                niederschlag REAL,
                wettercode INTEGER,
                FOREIGN KEY (stadt_id) REFERENCES staedte(id)
            )
        """)
        verbindung.execute("""
            CREATE TABLE IF NOT EXISTS prognose (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stadt_id INTEGER NOT NULL,
                datum TEXT NOT NULL,
                temperatur_min REAL,
                temperatur_max REAL,
                niederschlag REAL,
                wettercode INTEGER,
                FOREIGN KEY (stadt_id) REFERENCES staedte(id)
            )
        """)
        verbindung.commit()


def stadt_einfuegen(name, land, lat, lon):
    """Speichert eine neue Stadt. Gibt die id der neuen Zeile zurueck."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        cursor = verbindung.execute(
            "INSERT OR IGNORE INTO staedte (name, land, breitengrad, laengengrad) "
            "VALUES (?, ?, ?, ?)",
            (name, land, lat, lon)
        )
        verbindung.commit()
        return cursor.lastrowid


def stadt_loeschen(stadt_id):
    """Loescht eine Stadt und alle zugehoerigen Wetterdaten."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.execute("DELETE FROM wetterdaten WHERE stadt_id = ?", (stadt_id,))
        verbindung.execute("DELETE FROM prognose WHERE stadt_id = ?", (stadt_id,))
        verbindung.execute("DELETE FROM staedte WHERE id = ?", (stadt_id,))
        verbindung.commit()


def alle_staedte():
    """Liefert alle Staedte als Liste von Dicts."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.row_factory = sqlite3.Row
        return [dict(zeile) for zeile in
                verbindung.execute("SELECT * FROM staedte")]


def stadt_nach_id(stadt_id):
    """Liefert eine einzelne Stadt als Dict oder None."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.row_factory = sqlite3.Row
        ergebnis = verbindung.execute(
            "SELECT * FROM staedte WHERE id = ?", (stadt_id,)
        ).fetchone()
        return dict(ergebnis) if ergebnis else None


def wetterdaten_speichern(stadt_id, temperatur, windgeschwindigkeit, niederschlag, wettercode):
    """Speichert einen aktuellen Wetterdatensatz fuer eine Stadt."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.execute(
            "INSERT INTO wetterdaten "
            "(stadt_id, temperatur, windgeschwindigkeit, niederschlag, wettercode) "
            "VALUES (?, ?, ?, ?, ?)",
            (stadt_id, temperatur, windgeschwindigkeit, niederschlag, wettercode)
        )
        verbindung.commit()


def wetterdaten_nach_stadt(stadt_id):
    """Liefert alle gespeicherten Wetterdaten einer Stadt als Liste von Dicts."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.row_factory = sqlite3.Row
        return [dict(zeile) for zeile in
                verbindung.execute(
                    "SELECT * FROM wetterdaten WHERE stadt_id = ? ORDER BY abgerufen_am DESC",
                    (stadt_id,)
                )]


def prognose_speichern(stadt_id, datum, temp_min, temp_max, niederschlag, wettercode):
    """Speichert einen Prognosedatensatz fuer eine Stadt und ein Datum."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.execute(
            "INSERT INTO prognose "
            "(stadt_id, datum, temperatur_min, temperatur_max, niederschlag, wettercode) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (stadt_id, datum, temp_min, temp_max, niederschlag, wettercode)
        )
        verbindung.commit()


def prognose_nach_stadt(stadt_id):
    """Liefert alle gespeicherten Prognosedaten einer Stadt als Liste von Dicts."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.row_factory = sqlite3.Row
        return [dict(zeile) for zeile in
                verbindung.execute(
                    "SELECT * FROM prognose WHERE stadt_id = ? ORDER BY datum ASC",
                    (stadt_id,)
                )]


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