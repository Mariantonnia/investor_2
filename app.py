import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()

# Inicializar el analizador de sentimientos de VADER
analyzer = SentimentIntensityAnalyzer()

def obtener_sentimiento(texto):
    return analyzer.polarity_scores(texto)

# Noticias
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

indices_esg = {
    "Ambiental": [0, 5],
    "Social": [1, 6],
    "Gobernanza": [2, 8],
    "Riesgo": [3, 4, 7]
}

# Inicializar session state
if "contador" not in st.session_state:
    st.session_state.contador = 0
    st.session_state.reacciones = {cat: [] for cat in indices_esg.keys()}

title = "Análisis de Sentimiento de Inversores"
st.title(title)

# Proceso de preguntas y recolección de datos
if st.session_state.contador < len(noticias):
    noticia = noticias[st.session_state.contador]
    st.write(f"**Titular:** {noticia}")
    
    reaccion = st.text_input("¿Cuál es tu reacción a esta noticia?", key=f"reaccion_{st.session_state.contador}")
    
    if reaccion:
        texto_analizar = noticia + " " + reaccion
        sentimiento = obtener_sentimiento(texto_analizar)
        st.write(f"**Análisis de Sentimiento:** {sentimiento}")
        
        for categoria, indices in indices_esg.items():
            if st.session_state.contador in indices:
                st.session_state.reacciones[categoria].append(sentimiento)
        
        st.session_state.contador += 1
        st.rerun()
else:
    puntuaciones = {}
    
    for categoria, sentimientos in st.session_state.reacciones.items():
        if sentimientos:
            valores_pos = sum(s['pos'] for s in sentimientos) / len(sentimientos)
            valores_neg = sum(s['neg'] for s in sentimientos) / len(sentimientos)
            puntuacion = (valores_pos / (valores_pos + valores_neg + 0.0001)) * 100
            puntuaciones[categoria] = round(max(0, min(100, puntuacion)), 2)
        else:
            puntuaciones[categoria] = 50  # Valor neutro si no hay datos
    
    st.write("**Perfil del Inversor:**")
    for categoria, puntaje in puntuaciones.items():
        st.write(f"{categoria}: {puntaje}")
    
    # Graficar
    fig, ax = plt.subplots()
    ax.bar(puntuaciones.keys(), puntuaciones.values(), color=['green', 'blue', 'purple', 'red'])
    ax.set_ylabel("Puntuación (0-100)")
    ax.set_title("Perfil del Inversor")
    st.pyplot(fig)
    
    # Guardar en Google Sheets
    try:
        creds_json_str = st.secrets["gcp_service_account"]
        creds_json = json.loads(creds_json_str)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        sheet = client.open('BBDD_RESPUESTAS').get_worksheet(1)
        fila = [puntuaciones.get(cat, 50) for cat in ["Ambiental", "Social", "Gobernanza", "Riesgo"]]
        sheet.append_row(fila)
        st.success("Respuestas y perfil guardados en Google Sheets.")
    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}")
