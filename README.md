# 🌍 City Weather Dashboard

## Beschreibung
Die Anwendung richtet sich an Nutzerinnen und Nutzer, die aktuellen Wetterdaten und eine
 7-Tage-Prognose mehrerer Städte auf einen Blick vergleichen möchten. Bei Ausfall von Open-Meteo
 springt automatisch
wttr.in als Fallback-API ein. Die Auswertung zeigt die sonnigste, verregnetste,
wärmste und kälteste Stadt im Vergleich.

## Voraussetzungen
- Python 3.10 oder höher
- Internetverbindung (für API-Abrufe)
- Alle Bibliotheken siehe `requirements.txt`

## Installation

1. Repository klonen:
```
git clone https://github.com/sudo-mach-hinne/staedte_dashboard.git
cd staedte_dashboard
```

2. Virtuelle Umgebung anlegen und aktivieren:
```
python -m venv .venv
.venv\Scripts\activate
```
Bei PowerShell-Fehler (einmalig):
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. Bibliotheken installieren:
```
pip install -r requirements.txt
```

4. Konfiguration — `.env.example` nach `.env` kopieren:
```
copy .env.example .env
```

## Bedienung

Anwendung starten:
```
streamlit run app.py
```
Die App öffnet sich automatisch im Browser unter http://localhost:8501

### Seiten

| Seite | Funktion |
|---|---|
| Wetter abrufen | Stadtname eingeben, aktuelles Wetter und 7-Tage-Prognose mit Icons abrufen |
| Meine Städte | Alle gespeicherten Städte anzeigen und löschen |
| Städtevergleich | Mehrere Städte anhand von Prognosedaten vergleichen |

## Projektstruktur

```
staedte_dashboard/
├── app.py              # Streamlit-Frontend
├── api_client.py       # API-Abrufe (Open-Meteo)
├── datenbank.py        # SQLite-Datenbankzugriff
├── logik.py            # Berechnungen mit pandas
├── main.py             # Einstiegspunkt
├── test_api_wetter.py  # API-Schnelltest
├── daten/              # SQLite-Datenbankdatei (wird automatisch angelegt)
├── .env                # Lokale Konfiguration (nicht in Git)
├── .env.example        # Konfigurationsvorlage
├── .gitignore          # Git-Ausschlussliste
└── requirements.txt    # Bibliotheken und Versionen
```

## Verwendete APIs

| API | URL | Verwendung |
|---|---|---|
| Open-Meteo Forecast | https://api.open-meteo.com/v1/forecast | Wetterdaten und Prognose |
| Open-Meteo Geocoding | https://geocoding-api.open-meteo.com/v1/search | Koordinaten aus Stadtnamen |
| wttr.in | https://wttr.in | Fallback bei Open-Meteo-Ausfall |

Alle APIs sind kostenlos und benötigen keinen API-Schlüssel.

## Hinweise zum Datenschutz
- Es werden keine personenbezogenen Daten erfasst oder gespeichert.
- Gespeichert werden ausschließlich Städtenamen, Koordinaten und Wetterdaten.
- Die Datenbank liegt lokal unter `daten/projekt.db`.
- API-Schlüssel werden in `.env` gespeichert und nicht in Git hochgeladen.

## Online-Demo
https://staedtedashboard-4uuuttdjh5rcy9k7ht3bhw.streamlit.app/

## Autorin
Anne-Katrin Dittmann  
FIAE Umschulung – Robotron Bildungszentrum Leipzig  
Juni 2026