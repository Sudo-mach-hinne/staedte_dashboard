"""
Modulname: datenbank.py
Beschreibung: SQLite-Zugriff
Autor: Anne-Katrin Dittmann
Datum: 2. Juni 2026
"""

import sqlite3
from contextlib import closing

DB_PFAD = "daten/projekt.db"

def initialisiere_datenbank():
    """Legt die Tabellen an, falls sie noch nicht existieren."""
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
        verbindung.commit()

def stadt_einfuegen(name, land, lat, lon):
    """Speichert eine neue Stadt."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.execute(
            "INSERT INTO staedte (name, land, breitengrad, laengengrad) "
            "VALUES (?, ?, ?, ?)",
            (name, land, lat, lon)
        )
        verbindung.commit()

def alle_staedte():
    """Liefert alle Staedte als Liste von Dicts."""
    with closing(sqlite3.connect(DB_PFAD)) as verbindung:
        verbindung.row_factory = sqlite3.Row
        return [dict(zeile) for zeile in
                verbindung.execute("SELECT * FROM staedte")]
    
if __name__ == "__main__":
    initialisiere_datenbank()
    stadt_einfuegen("Leipzig", "Deutschland", 51.3397, 12.3731)
    stadt_einfuegen("Berlin", "Deutschland", 52.5200, 13.4050)
    print(alle_staedte())