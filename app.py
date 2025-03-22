import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()

analyzer = SentimentIntensityAnalyzer()

def obtener_sentimiento(texto):
    return analyzer.polarity_scores(texto)

def asignar_puntuacion(compound, categoria):
    if categoria in ["Ambiental", "Gobernanza", "Riesgo"]:
        return 100 if compound <= -0.03 else 90 if compound <= -0.025 else 80 if compound <= -0.02 else 70 if compound <= -0.015 else 60 if compound <= -0.01 else 50 if compound <= 0 else 40 if compound <= 0.1 else 30 if compound <= 0.2 else 20 if compound <= 0.4 else 10 if compound <= 0.5 else 0
    elif categoria == "Social":
        return 100 if compound >= 0.025 else 90 if compound >= 0.02 else 80 if compound >= 0.015 else 70 if compound >= 0.01 else 60 if compound >= 0.05 else 50 if compound >= 0 else 40 if compound >= -0.01 else 30 if compound >= -0.02 else 20 if compound >= -0.03 else 10 if compound >= -0.04 else 0

noticias = [
    "Repsol, entre las 50 empresas que más responsabilidad histórica tienen en el calentamiento global",
    "Amancio Ortega crea un fondo de 100 millones de euros para los afectados de la dana",
    "Freshly Cosmetics despide a 52 empleados en Reus, el 18% de la plantilla",
    "Wall Street y los mercados globales caen ante la incertidumbre por la guerra comercial y el temor a una recesión",
    "El mercado de criptomonedas se desploma: Bitcoin cae a 80.000 dólares, las altcoins se hunden en medio de una frenética liquidación",
    "Granada retrasa seis meses el inicio de la Zona de Bajas Emisiones, previsto hasta ahora para abril",
    "McDonald's donará a la Fundación Ronald McDonald todas las ganancias por ventas del Big Mac del 6 de diciembre",
    "El Gobierno autoriza a altos cargos públicos a irse a Indra, Escribano, CEOE, Barceló, Iberdrola o Airbus",
    "Las aportaciones a los planes de pensiones caen 10.000 millones en los últimos cuatro años",
]

if "contador" not in st.session_state:
    st.session_state.contador = 0
    st.session_state.reacciones = {}

title = "Chatbot de Análisis de Sentimiento"
st.title(title)

if st.session_state.contador < len(noticias):
    noticia = noticias[st.session_state.contador]
    st.chat_message("assistant").write(f"**Noticia:** {noticia}")
    user_input = st.chat_input("Escribe tu reacción")
    
    if user_input:
        sentimiento = obtener_sentimiento(user_input)
        st.session_state.reacciones[st.session_state.contador] = {"texto": user_input, "sentimiento": sentimiento}
        st.chat_message("user").write(user_input)
        st.chat_message("assistant").write(f"**Análisis de Sentimiento:** {sentimiento}")
        
        st.session_state.contador += 1
        st.rerun()
else:
    puntuaciones = {"Ambiental": 50, "Social": 50, "Gobernanza": 50, "Riesgo": 50}
    e_scores, s_scores, g_scores, r_scores = [], [], [], []
    
    for i, sentimiento in st.session_state.reacciones.items():
        compound = sentimiento['sentimiento']['compound']
        if i in [0, 5]:
            e_scores.append(asignar_puntuacion(compound, "Ambiental"))
        elif i in [1, 6]:
            s_scores.append(asignar_puntuacion(compound, "Social"))
        elif i in [2, 7]:
            g_scores.append(asignar_puntuacion(compound, "Gobernanza"))
        elif i in [3, 4, 8]:
            r_scores.append(asignar_puntuacion(compound, "Riesgo"))
    
    if e_scores:
        puntuaciones["Ambiental"] = round(sum(e_scores) / len(e_scores))
    if s_scores:
        puntuaciones["Social"] = round(sum(s_scores) / len(s_scores))
    if g_scores:
        puntuaciones["Gobernanza"] = round(sum(g_scores) / len(g_scores))
    if r_scores:
        puntuaciones["Riesgo"] = round(sum(r_scores) / len(r_scores))
    
    st.chat_message("assistant").write("**Perfil del Inversor:**")
    for categoria, puntaje in puntuaciones.items():
        st.chat_message("assistant").write(f"{categoria}: {puntaje}")
    
    fig, ax = plt.subplots()
    ax.bar(puntuaciones.keys(), puntuaciones.values(), color=['green', 'blue', 'purple', 'red'])
    ax.set_ylabel("Puntuación (0-100)")
    ax.set_title("Perfil del Inversor")
    st.pyplot(fig)
    
    try:
        creds_json_str = st.secrets["gcp_service_account"]
        creds_json = json.loads(creds_json_str)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        sheet = client.open('BBDD_RESPUESTAS').get_worksheet(1)
        fila = [puntuaciones.get(cat, 50) for cat in ["Ambiental", "Social", "Gobernanza", "Riesgo"]]
        reacciones_lista = [st.session_state.reacciones.get(i, {}).get('texto', 'Sin reacción') for i in range(len(noticias))]
        fila.extend(reacciones_lista)
        sheet.append_row(fila)
        st.chat_message("assistant").write("Respuestas y perfil guardados en Google Sheets.")
    except Exception as e:
        st.chat_message("assistant").write(f"Error al guardar en Google Sheets: {e}")
