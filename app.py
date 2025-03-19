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

# Inicializar session state
if "contador" not in st.session_state:
    st.session_state.contador = 0
    st.session_state.reacciones = {}

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
        
        st.session_state.reacciones[st.session_state.contador] = sentimiento
        st.session_state.contador += 1
        st.rerun()
else:
    puntuaciones = {"Ambiental": 50, "Social": 50, "Gobernanza": 50, "Riesgo": 50}
    
    if st.session_state.reacciones:
        # Calcular puntuaciones según la lógica definida
        e_scores = [st.session_state.reacciones[i]['pos'] - st.session_state.reacciones[i]['neg'] for i in [0, 5] if i in st.session_state.reacciones]
        s_scores = [st.session_state.reacciones[i]['pos'] - st.session_state.reacciones[i]['neg'] for i in [1, 6] if i in st.session_state.reacciones]
        g_scores = [-st.session_state.reacciones[2]['neg'] + st.session_state.reacciones[8]['pos']] if 2 in st.session_state.reacciones and 8 in st.session_state.reacciones else []
        r_scores = [1 - st.session_state.reacciones[i]['pos'] for i in [3, 4, 7] if i in st.session_state.reacciones]
        
        # Normalizar valores
        if e_scores:
            puntuaciones["Ambiental"] = max(0, min(100, (sum(e_scores) / len(e_scores)) * 100))
        if s_scores:
            puntuaciones["Social"] = max(0, min(100, (sum(s_scores) / len(s_scores)) * 100))
        if g_scores:
            puntuaciones["Gobernanza"] = max(0, min(100, (sum(g_scores) / len(g_scores)) * 100))
        if r_scores:
            puntuaciones["Riesgo"] = max(0, min(100, (sum(r_scores) / len(r_scores)) * 100))
    
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
