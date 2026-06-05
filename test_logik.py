"""
Modulname: test_logik.py
Beschreibung: Unit-Tests fuer logik.py mit pytest.
              Getestet werden Berechnungsfunktionen und das Wettericon-Mapping.
              Kein Datenbankzugriff, keine API-Aufrufe — alle Tests laufen offline.
Autor: Anne-Katrin Dittmann
Datum: Juni 2026

Ausfuehren:
    pytest test_logik.py -v
"""

import pytest
from logik import (
    durchschnittstemperatur,
    temperatur_extremwerte,
    staedte_vergleich,
    prognose_als_dataframe,
    wettercode_zu_icon,
)


# ---------------------------------------------------------------------------
# Tests: durchschnittstemperatur()
# ---------------------------------------------------------------------------

def test_durchschnittstemperatur_normal():
    """Berechnung des Durchschnitts aus drei Wetterdatensaetzen."""
    daten = [
        {"temperatur": 10.0},
        {"temperatur": 20.0},
        {"temperatur": 30.0},
    ]
    # Erwarteter Durchschnitt: (10 + 20 + 30) / 3 = 20.0
    assert durchschnittstemperatur(daten) == 20.0


def test_durchschnittstemperatur_einzelwert():
    """Einzelner Datensatz -- Durchschnitt entspricht dem Wert selbst."""
    daten = [{"temperatur": 15.5}]
    assert durchschnittstemperatur(daten) == 15.5


def test_durchschnittstemperatur_leer():
    """Leere Liste gibt None zurueck, kein Absturz."""
    assert durchschnittstemperatur([]) is None


def test_durchschnittstemperatur_negative_werte():
    """Auch negative Temperaturen (Winter) werden korrekt berechnet."""
    daten = [
        {"temperatur": -5.0},
        {"temperatur": -3.0},
        {"temperatur": -1.0},
    ]
    # Erwarteter Durchschnitt: (-5 + -3 + -1) / 3 = -3.0
    assert durchschnittstemperatur(daten) == -3.0


# ---------------------------------------------------------------------------
# Tests: temperatur_extremwerte()
# ---------------------------------------------------------------------------

def test_temperatur_extremwerte_normal():
    """Minimum und Maximum werden korrekt aus den Daten ermittelt."""
    daten = [
        {"temperatur": 18.5},
        {"temperatur": 21.0},
        {"temperatur": 15.3},
    ]
    ergebnis = temperatur_extremwerte(daten)
    assert ergebnis["minimum"] == 15.3
    assert ergebnis["maximum"] == 21.0


def test_temperatur_extremwerte_leer():
    """Leere Liste gibt None zurueck."""
    assert temperatur_extremwerte([]) is None


def test_temperatur_extremwerte_einzelwert():
    """Bei einem einzigen Wert sind Minimum und Maximum identisch."""
    daten = [{"temperatur": 12.0}]
    ergebnis = temperatur_extremwerte(daten)
    assert ergebnis["minimum"] == 12.0
    assert ergebnis["maximum"] == 12.0


# ---------------------------------------------------------------------------
# Tests: wettercode_zu_icon()
# ---------------------------------------------------------------------------

def test_wettercode_sonnig():
    """Wettercode 0 = klarer Himmel."""
    assert wettercode_zu_icon(0) == "wi wi-day-sunny"


def test_wettercode_teilbewoelkt():
    """Wettercodes 1 und 2 = teilweise bewoelkt."""
    assert wettercode_zu_icon(1) == "wi wi-day-cloudy"
    assert wettercode_zu_icon(2) == "wi wi-day-cloudy"


def test_wettercode_bewoelkt():
    """Wettercode 3 = bedeckt."""
    assert wettercode_zu_icon(3) == "wi wi-cloudy"


def test_wettercode_regen():
    """Wettercodes 51-67 = Regen / Nieselregen."""
    assert wettercode_zu_icon(51) == "wi wi-rain"
    assert wettercode_zu_icon(61) == "wi wi-rain"


def test_wettercode_schnee():
    """Wettercodes 71-77 = Schneefall."""
    assert wettercode_zu_icon(71) == "wi wi-snow"


def test_wettercode_schauer():
    """Wettercodes 80-82 = Regenschauer."""
    assert wettercode_zu_icon(80) == "wi wi-showers"


def test_wettercode_gewitter():
    """Wettercodes 95-99 = Gewitter."""
    assert wettercode_zu_icon(95) == "wi wi-thunderstorm"


def test_wettercode_unbekannt():
    """Unbekannter Wettercode gibt Standard-Fallback-Icon zurueck, kein Absturz."""
    assert wettercode_zu_icon(999) == "wi wi-na"


def test_wettercode_negativer_wert():
    """Negativer Wettercode wird als unbekannt behandelt."""
    assert wettercode_zu_icon(-1) == "wi wi-na"


# ---------------------------------------------------------------------------
# Tests: staedte_vergleich()
# ---------------------------------------------------------------------------

def test_staedte_vergleich_normal():
    """Vergleich von zwei Staedten -- waermere Stadt steht oben."""
    daten = [
        {
            "name": "Leipzig",
            "prognose": [
                {"temperatur_max": 20.0, "temperatur_min": 12.0, "niederschlag": 0.5},
                {"temperatur_max": 22.0, "temperatur_min": 14.0, "niederschlag": 0.0},
            ]
        },
        {
            "name": "Tokio",
            "prognose": [
                {"temperatur_max": 30.0, "temperatur_min": 22.0, "niederschlag": 1.0},
                {"temperatur_max": 32.0, "temperatur_min": 24.0, "niederschlag": 0.5},
            ]
        },
    ]
    df = staedte_vergleich(daten)
    # Tokio ist waermer -- muss an erster Stelle stehen
    assert df.iloc[0]["name"] == "Tokio"
    assert df.iloc[1]["name"] == "Leipzig"


def test_staedte_vergleich_leer():
    """Leere Eingabe gibt leeren DataFrame zurueck."""
    df = staedte_vergleich([])
    assert df.empty


def test_staedte_vergleich_ohne_prognose():
    """Stadt ohne Prognosedaten wird uebersprungen."""
    daten = [
        {"name": "Leipzig", "prognose": []},
    ]
    df = staedte_vergleich(daten)
    assert df.empty


# ---------------------------------------------------------------------------
# Tests: prognose_als_dataframe()
# ---------------------------------------------------------------------------

def test_prognose_als_dataframe_sortierung():
    """Prognosedaten werden nach Datum aufsteigend sortiert."""
    prognose = [
        {"datum": "2026-06-03", "temperatur_min": 10.0, "temperatur_max": 18.0, "niederschlag": 0.0, "wettercode": 1},
        {"datum": "2026-06-01", "temperatur_min": 12.0, "temperatur_max": 20.0, "niederschlag": 0.2, "wettercode": 2},
        {"datum": "2026-06-02", "temperatur_min": 11.0, "temperatur_max": 19.0, "niederschlag": 0.0, "wettercode": 0},
    ]
    df = prognose_als_dataframe(prognose)
    # Erster Eintrag muss das frueheste Datum sein
    assert str(df.iloc[0]["datum"].date()) == "2026-06-01"


def test_prognose_als_dataframe_leer():
    """Leere Prognoseliste gibt leeren DataFrame zurueck."""
    df = prognose_als_dataframe([])
    assert df.empty