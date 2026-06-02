#"""
#Modulname: app.py
#Beschreibung: Streamlit-Frontend
#Autor: Anne-Katrin Dittmann
#Datum: 2. Juni 2026
#"""

"""
app.py -- Streamlit-Frontend (Hallo-Welt-Version)
Autor: Anne-Katrin Dittmann
Datum: 2. Juni 2026
"""
import streamlit as st

# Seitentitel und Layout festlegen
st.set_page_config(page_title="Mein Projekt", layout="wide")

# Hauptueberschrift
st.title("Hallo, Streamlit!")

# Einfache Eingabe
name = st.text_input("Wie heißen Sie?", placeholder="Ihr Name")

# Reaktion auf Eingabe
if name:
    st.success(f"Willkommen, {name}! Die App laeuft.")

# Trennlinie und Hinweis
st.divider()
st.info("Diese App wird in den nächsten Tagen ausgebaut.")