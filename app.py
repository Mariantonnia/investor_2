import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langchain_groq import ChatGroq
import os
import json
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()

# Configurar el modelo LLM
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    model="gemma2-9b-it",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

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

# Inicializar el analizador de sentimientos de VADER
analyzer = SentimentIntensityAnalyzer()

def obtener_sentimiento(texto):
    return analyzer.polarity_scores(texto)

indices_esg = {
    "Ambiental": [0, 5],
    "Social": [1, 6],
    "Gobernanza": [2, 8],
    "Riesgo": [3, 4, 8]
}

if "contador" not in st.session_state:
    st.session_state.contador = 0
    st.session_state.reacciones = []
    st.session_state.titulares = []

st.title("Análisis de Sentimiento de Inversores")

if st.session_state.contador < len(noticias):
    noticia = noticias[st.session_state.contador]
    st.session_state.titulares.append(noticia)
    st.write(f"**Titular:** {noticia}")
    
    reaccion = st.text_input(f"¿Cuál es tu reacción a esta noticia?", key=f"reaccion_{st.session_state.contador}")
    
    if reaccion:
        texto_analizar = noticia + " " + reaccion  # Combinar titular y reacción
        sentimiento = obtener_sentimiento(texto_analizar)
        st.write(f"**Análisis de Sentimiento:** {sentimiento}")
        
        st.session_state.reacciones.append(reaccion)
        st.session_state.contador += 1
        st.rerun()
else:
    puntuaciones = {}
    
    for categoria, indices in indices_esg.items():
        valores = {"pos": [], "neu": [], "neg": []}
        for i in indices:
            if i < len(st.session_state.reacciones):
                texto_analizar = noticias[i] + " " + st.session_state.reacciones[i]
                sentimiento = obtener_sentimiento(texto_analizar)
                valores["pos"].append(sentimiento['pos'])
                valores["neu"].append(sentimiento['neu'])
                valores["neg"].append(sentimiento['neg'])
        
        if valores["pos"] or valores["neg"]:
            puntuacion = valores["pos"] #(sum(valores["pos"]) / (sum(valores["pos"]) + sum(valores["neg"]) + 0.0001)) * 100
            puntuaciones[categoria] = max(0, min(100, puntuacion))
    
    st.write(f"**Perfil del inversor:** {valores["pos"]}")
    
    categorias = list(puntuaciones.keys())
    valores = list(puntuaciones.values())
    
    fig, ax = plt.subplots()
    ax.bar(categorias, valores)
    ax.set_ylabel("Puntuación (0-100)")
    ax.set_title("Perfil del Inversor")
    st.pyplot(fig)
    
    try:
        creds_json_str = st.secrets["gcp_service_account"]
        creds_json = json.loads(creds_json_str)
    except Exception as e:
        st.error(f"Error al cargar las credenciales: {e}")
        st.stop()
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    
    sheet = client.open('BBDD_RESPUESTAS').get_worksheet(1)
    fila = st.session_state.reacciones[:]
    fila.extend([puntuaciones.get("Ambiental", 0), puntuaciones.get("Social", 0), puntuaciones.get("Gobernanza", 0), puntuaciones.get("Riesgo", 0)])
    sheet.append_row(fila)
    st.success("Respuestas y perfil guardados en Google Sheets en una misma fila.")
