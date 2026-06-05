# 🌍 City Weather Dashboard

## Beschreibung

Das City Weather Dashboard ist eine webbasierte Anwendung zum Abrufen, Speichern und Vergleichen von Wetterdaten beliebiger Städte weltweit. Die Anwendung zeigt aktuelle Wetterdaten sowie eine 7-Tage-Prognose, speichert diese persistent in einer lokalen SQLite-Datenbank und wertet sie statistisch aus. Alle gespeicherten Städte werden zusätzlich auf einer interaktiven Weltkarte dargestellt.

Bei Ausfall von Open-Meteo springt automatisch wttr.in als Fallback-API ein. Die Auswertung zeigt die sonnigste, verregnetste, wärmste und kälteste Stadt im Vergleich.

## Voraussetzungen

- Python 3.10 oder höher
- Internetverbindung (für API-Abrufe)
- Alle Bibliotheken siehe requirements.txt

## Installation

1. Repository klonen:

        git clone https://github.com/sudo-mach-hinne/staedte_dashboard.git
        cd staedte_dashboard

2. Virtuelle Umgebung anlegen und aktivieren:

        python -m venv .venv
        .venv\Scripts\activate

   Bei PowerShell-Fehler (einmalig ausführen):

        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

3. Bibliotheken installieren:

        pip install -r requirements.txt

4. Konfiguration — .env.example nach .env kopieren:

        copy .env.example .env

## Anwendung starten

        streamlit run app.py

Die App öffnet sich automatisch im Browser unter http://localhost:8501

## Bedienung

- Stadtname ins Eingabefeld eingeben und auf Hinzufügen klicken
- Bei mehreren Treffern (z. B. "Frankfurt") erscheint eine Auswahl
- Jede Stadt zeigt aktuelles Wetter, Wettericon, Temperatur, Wind, Ø-Temperatur und 7-Tage-Prognose
- Die Weltkarte zeigt alle Städte als anklickbare Pins mit Wetter- und Länderinformationen
- Ab zwei Städten erscheint automatisch ein Vergleich: sonnigste, verregnetste, wärmste und kälteste Stadt

## Projektstruktur

    staedte_dashboard/
    ├── app.py                  # Streamlit-Frontend
    ├── api_client.py           # API-Abrufe (Open-Meteo, wttr.in, REST Countries, Geocoding)
    ├── datenbank.py            # SQLite-Datenbankzugriff
    ├── logik.py                # Berechnungen mit pandas, Wettericon-Mapping
    ├── main.py                 # Einstiegspunkt
    ├── Clouds_background.jpg   # Hintergrundbild
    ├── daten/
    │   └── projekt.db          # SQLite-Datenbank (wird automatisch angelegt)
    ├── .env                    # Lokale Konfiguration (nicht in Git)
    ├── .env.example            # Konfigurationsvorlage
    ├── .gitignore              # Git-Ausschlussliste
    └── requirements.txt        # Bibliotheken und Versionen

## Verwendete APIs

| API | URL | Verwendung |
|---|---|---|
| Open-Meteo Forecast | https://api.open-meteo.com/v1/forecast | Aktuelle Wetterdaten und 7-Tage-Prognose |
| Open-Meteo Geocoding | https://geocoding-api.open-meteo.com/v1/search | Koordinaten aus Stadtnamen |
| wttr.in | https://wttr.in | Fallback bei Open-Meteo-Ausfall |
| REST Countries | https://restcountries.com/v3.1 | Hauptstadt, Währung, Sprache |
| OpenStreetMap / folium | https://openstreetmap.org | Interaktive Weltkarte |

Alle APIs sind kostenlos und benötigen keinen API-Schlüssel.

## Hinweise zum Datenschutz

- Es werden keine personenbezogenen Daten erfasst oder gespeichert.
- Gespeichert werden ausschließlich Städtenamen, Koordinaten und Wetterdaten.
- Die Datenbank liegt lokal unter daten/projekt.db.
- Konfigurationswerte werden in .env gespeichert und nicht in Git hochgeladen.

## Online-Demo

https://staedtedashboard-4uuuttdjh5rcy9k7ht3bhw.streamlit.app

## Autorin

Anne-Katrin Dittmann
FIAE Umschulung – Robotron Bildungszentrum Leipzig
Juni 2026
