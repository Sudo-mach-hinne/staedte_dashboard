"""
Modulname: main.py

Beschreibung: Einstiegspunkt der Anwendung.
Startet die Streamlit-App (app.py) programmatisch.
Weil Streamlit-Apps ueber den streamlit-Befehl laufen und nicht
ueber "python <datei>", ruft main.py hier intern denselben
Befehl auf. So laesst sich das Projekt sowohl mit
"python main.py" als auch mit "streamlit run app.py" starten.

Autor: Anne-Katrin Dittmann
Datum: Juni 2026
"""

import os
import sys

from streamlit.web import cli as stcli


if __name__ == "__main__":
    # Pfad zu app.py relativ zu dieser Datei bestimmen, damit der Start
    # auch dann klappt, wenn man aus einem anderen Verzeichnis aufruft.
    hier = os.path.dirname(os.path.abspath(__file__))
    app_pfad = os.path.join(hier, "app.py")

    # sys.argv so setzen, als haette man "streamlit run app.py" eingetippt.
    sys.argv = ["streamlit", "run", app_pfad]
    sys.exit(stcli.main())