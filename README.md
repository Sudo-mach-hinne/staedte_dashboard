# 🌍 City Weather Dashboard

## Beschreibung

Das City Weather Dashboard ist eine webbasierte Anwendung zum Abrufen, Speichern und Vergleichen von Wetterdaten beliebiger Städte weltweit. Die Anwendung zeigt aktuelle Wetterdaten sowie eine 7-Tage-Prognose, speichert diese persistent in einer lokalen SQLite-Datenbank und wertet sie statistisch aus. Alle gespeicherten Städte werden zusätzlich auf einer interaktiven Weltkarte dargestellt.

Fällt die primäre Wetter-API (Open-Meteo) aus, springt automatisch wttr.in als Fallback ein. Die Auswertung benennt die sonnigste, verregnetste, wärmste und kälteste Stadt im Vergleich. Über die Navigation sind vier weitere Seiten erreichbar: stündliches Wetter, Niederschlagsradar, Reisewetter und historisches Wetter.

## Funktionsüberblick

- Städte per Namenssuche hinzufügen; bei mehrdeutigen Namen (z. B. mehrere „Dresden“) erscheint eine Auswahl mit Region und Land
- Gleichnamige Orte an unterschiedlichen Koordinaten lassen sich getrennt hinzufügen und vergleichen
- Aktuelles Wetter, Wettericon, Temperatur, Wind, Durchschnittstemperatur und 7-Tage-Prognose je Stadt
- Interaktive Weltkarte mit anklickbaren Pins (Wetter- und Länderinformationen)
- Automatischer Städtevergleich mit Superlativen und sortierter Übersichtstabelle
- Automatischer Fallback auf eine zweite Wetter-API bei Ausfall der ersten
- Umschaltbares Hell-/Dunkel-Design
- Persistente Speicherung in SQLite; Auswertungen mit pandas
- Unit-Tests mit pytest

## Voraussetzungen

- Python 3.10 oder höher
- Internetverbindung (für die API-Abrufe)
- Alle Bibliotheken siehe `requirements.txt`

## Installation

1. Repository klonen:

        git clone https://github.com/Sudo-mach-hinne/staedte_dashboard.git
        cd staedte_dashboard

2. Virtuelle Umgebung anlegen und aktivieren:

        python -m venv .venv
        .venv\Scripts\activate

    Bei einem PowerShell-Fehler zur Ausführungsrichtlinie (einmalig):

        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

3. Bibliotheken installieren:

        pip install -r requirements.txt

4. Konfiguration anlegen — `.env.example` nach `.env` kopieren:

        copy .env.example .env

## Anwendung starten

Die Anwendung lässt sich auf zwei Wegen starten:

        streamlit run app.py

oder über den Einstiegspunkt:

        python main.py

Die App öffnet sich anschließend automatisch im Browser unter http://localhost:8501

## Bedienung

**Hauptseite**

- Stadtname ins Eingabefeld eingeben und auf „Hinzufügen“ klicken (Enter funktioniert ebenfalls)
- Bei mehreren Treffern (z. B. „Leipzig“ oder mehrere „Dresden“) erscheint eine Auswahl mit Region und Land
- Jede Stadt zeigt aktuelles Wetter, Wettericon, Temperatur, Wind, Durchschnittstemperatur und 7-Tage-Prognose
- Die Weltkarte zeigt alle Städte als anklickbare Pins mit Wetter- und Länderinformationen
- Ab zwei Städten erscheint automatisch ein Vergleich: sonnigste, verregnetste, wärmste und kälteste Stadt sowie eine Übersichtstabelle
- Über den Design-Umschalter lässt sich zwischen hellem und dunklem Erscheinungsbild wechseln

**Weitere Seiten (Navigation links)**

- **Stündliches Wetter:** Ort eingeben, stündlicher Verlauf von Temperatur und Niederschlag als kombiniertes Diagramm
- **Niederschlagsradar:** Ort eingeben, Radar-Niederschlag der letzten zwei Stunden als Karten-Overlay, gesteuert über einen Zeitschieberegler; zusätzlich stündliche Vorhersage als farbige Marker
- **Reisewetter:** Reiseziel eingeben, Klimaübersicht mit Monatsdiagrammen für Temperatur und Niederschlag (Durchschnitt 1991–2020)
- **Historisches Wetter:** Ort eingeben, Zeitraum wählen, Temperatur- und Niederschlagsverlauf als Diagramm (Daten ab 1940)

## Projektstruktur

    staedte_dashboard/
    ├── app.py                      # Streamlit-Frontend (Hauptseite)
    ├── main.py                     # Einstiegspunkt, startet app.py
    ├── api_client.py               # API-Abrufe (Open-Meteo, wttr.in, REST Countries, RainViewer)
    ├── datenbank.py                # SQLite-Datenbankzugriff
    ├── logik.py                    # Berechnungen mit pandas, Wettericon-Mapping
    ├── stil.py                     # Zentrales CSS/Styling, Hell-/Dunkel-Design
    ├── pages/
    │   ├── 1_Stündliches_Wetter.py   # Stündlicher Temperatur-/Niederschlagsverlauf
    │   ├── 2_Niederschlagsradar.py   # Radar-Overlay (RainViewer) + Vorhersage
    │   ├── 3_Reisewetter.py          # Klimaübersicht für Reiseziele
    │   └── 4_Historisches_Wetter.py  # Historische Wetterdaten mit Diagrammen
    ├── test_logik.py               # Unit-Tests für die Berechnungslogik
    ├── test_api_wetter.py          # Tests für die API-Anbindung
    ├── Clouds_background.jpg       # Hintergrundbild (helles Design)
    ├── Clouds_dark.jpg             # Hintergrundbild (dunkles Design)
    ├── daten/
    │   └── projekt.db              # SQLite-Datenbank (wird automatisch angelegt)
    ├── .env                        # Lokale Konfiguration (nicht in Git)
    ├── .env.example                # Konfigurationsvorlage
    ├── .gitignore                  # Git-Ausschlussliste
    ├── requirements.txt            # Bibliotheken und Versionen
    └── start.bat                   # Startskript für Windows

## Tests ausführen

        pytest

Getestet werden die Berechnungsfunktionen (Durchschnitt, Extremwerte, Städtevergleich, Wettericon-Mapping) und die API-Anbindung. Die Logik-Tests laufen vollständig offline.

## Verwendete APIs

| API                    | URL                                             | Verwendung                               |
| ---------------------- | ----------------------------------------------- | ---------------------------------------- |
| Open-Meteo Forecast    | https://api.open-meteo.com/v1/forecast          | Aktuelle Wetterdaten und 7-Tage-Prognose |
| Open-Meteo Geocoding   | https://geocoding-api.open-meteo.com/v1/search  | Koordinaten aus Stadtnamen               |
| Open-Meteo Archive     | https://archive-api.open-meteo.com/v1/archive   | Historische Wetterdaten ab 1940          |
| Open-Meteo Climate     | https://climate-api.open-meteo.com/v1/climate   | Klimadurchschnitte 1991–2020             |
| wttr.in                | https://wttr.in                                 | Fallback bei Open-Meteo-Ausfall          |
| REST Countries         | https://restcountries.com/v3.1                  | Hauptstadt, Währung, Sprache             |
| RainViewer             | https://api.rainviewer.com                      | Niederschlagsradar-Kacheln               |
| OpenStreetMap / folium | https://openstreetmap.org                       | Interaktive Karten                       |

Alle APIs sind kostenlos und benötigen keinen API-Schlüssel.

## Hinweise zum Datenschutz

- Es werden keine personenbezogenen Daten erfasst oder gespeichert.
- Gespeichert werden ausschließlich Städtenamen, Koordinaten und Wetterdaten.
- Die Datenbank liegt lokal unter `daten/projekt.db`.
- Konfigurationswerte werden in `.env` gespeichert und nicht in Git hochgeladen.
- Alle Datenbankabfragen sind parametrisiert (Schutz vor SQL-Injection).

## Online-Demo

https://staedtedashboard-4uuuttdjh5rcy9k7ht3bhw.streamlit.app

## Autorin

Anne-Katrin Dittmann
FIAE 25-02 – Robotron Bildungszentrum Leipzig
Juni 2026