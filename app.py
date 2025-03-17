import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langchain import LLMChain, PromptTemplate
from langchain_groq import ChatGroq
import os
import re
import matplotlib.pyplot as plt
import pandas as pd
import json
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

# Función para obtener sentimiento
def obtener_sentimiento(texto):
    sentimiento = analyzer.polarity_scores(texto)
    return sentimiento

# Plantilla y cadena para análisis de reacciones
plantilla_reaccion = """
Reacción del inversor: {reaccion}
Analiza el sentimiento y la preocupación expresada:
"""
prompt_reaccion = PromptTemplate(template=plantilla_reaccion, input_variables=["reaccion"])
cadena_reaccion = LLMChain(llm=llm, prompt=prompt_reaccion)

plantilla_perfil = """
Análisis de reacciones: {analisis}
Genera un perfil detallado del inversor basado en sus reacciones, enfocándote en los pilares ESG (Ambiental, Social y Gobernanza) y su aversión al riesgo. 
Asigna una puntuación de 0 a 100 para cada pilar ESG y para el riesgo, donde 0 indica ninguna preocupación y 100 máxima preocupación o aversión.
Devuelve las 4 puntuaciones en formato: Ambiental: [puntuación], Social: [puntuación], Gobernanza: [puntuación], Riesgo: [puntuación]
"""
prompt_perfil = PromptTemplate(template=plantilla_perfil, input_variables=["analisis"])
cadena_perfil = LLMChain(llm=llm, prompt=prompt_perfil)

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
        # Analizar sentimiento de la reacción
        sentimiento = obtener_sentimiento(reaccion)
        st.write(f"**Análisis de Sentimiento:** {sentimiento}")
        
        # Basado en el sentimiento, ajustar las puntuaciones ESG y Riesgo
        # Si el sentimiento es negativo, podemos aumentar el riesgo y disminuir el puntaje ESG
        if sentimiento['compound'] < -0.2:
            puntuaciones = {"Ambiental": 70, "Social": 60, "Gobernanza": 65, "Riesgo": 85}
        elif sentimiento['compound'] > 0.2:
            puntuaciones = {"Ambiental": 40, "Social": 40, "Gobernanza": 50, "Riesgo": 30}
        else:
            puntuaciones = {"Ambiental": 55, "Social": 50, "Gobernanza": 60, "Riesgo": 50}

        st.session_state.reacciones.append(reaccion)
        st.session_state.contador += 1
        st.rerun()
else:
    # Análisis de todas las reacciones
    analisis_total = ""
    for titular, reaccion in zip(st.session_state.titulares, st.session_state.reacciones):
        analisis_reaccion = cadena_reaccion.run(reaccion=reaccion)
        analisis_total += analisis_reaccion + "\n"

    perfil = cadena_perfil.run(analisis=analisis_total)
    st.write(f"**Perfil del inversor:** {perfil}")
    
    # Extraer puntuaciones del perfil con expresiones regulares
    puntuaciones = {
        "Ambiental": int(re.search(r"Ambiental: (\d+)", perfil).group(1)),
        "Social": int(re.search(r"Social: (\d+)", perfil).group(1)),
        "Gobernanza": int(re.search(r"Gobernanza: (\d+)", perfil).group(1)),
        "Riesgo": int(re.search(r"Riesgo: (\d+)", perfil).group(1)),
    }

    # Crear gráfico de barras
    categorias = list(puntuaciones.keys())
    valores = list(puntuaciones.values())

    fig, ax = plt.subplots()
    ax.bar(categorias, valores)
    ax.set_ylabel("Puntuación (0-100)")
    ax.set_title("Perfil del Inversor")
    st.pyplot(fig)

    try:
        # Cargar credenciales de Google Sheets
        creds_json_str = st.secrets["gcp_service_account"]
        creds_json = json.loads(creds_json_str)
    except Exception as e:
        st.error(f"Error al cargar las credenciales: {e}")
        st.stop()
    
    # Autorización con Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    
    # Abrir la hoja de cálculo
    sheet = client.open('BBDD_RESPUESTAS').get_worksheet(1)

    # Construir una sola fila con toda la información
    fila = []
    for titular, reaccion in zip(st.session_state.titulares, st.session_state.reacciones):
        fila.append(titular)
        fila.append(reaccion)
    
    # Agregar las puntuaciones al final
    fila.extend([
        puntuaciones["Ambiental"],
        puntuaciones["Social"],
        puntuaciones["Gobernanza"],
        puntuaciones["Riesgo"]
    ])

    # Agregar la fila a Google Sheets
    sheet.append_row(fila)

    st.success("Respuestas y perfil guardados en Google Sheets en una misma fila.")

