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
        #texto_analizar = noticia + " " + reaccion
        texto_analizar = reaccion
        sentimiento = obtener_sentimiento(texto_analizar)
        st.write(f"**Análisis de Sentimiento:** {sentimiento}")
        
        st.session_state.reacciones[st.session_state.contador] = sentimiento
        st.session_state.contador += 1
        st.rerun()
else:
    puntuaciones = {"Ambiental": 50, "Social": 50, "Gobernanza": 50, "Riesgo": 50}

    if st.session_state.reacciones:
        e_scores = []
        s_scores = []
        g_scores = []
        r_scores = []

        # Calcular puntuaciones según la nueva lógica
        for i, sentimiento in st.session_state.reacciones.items():
            if i in [0, 5]:  # Ambiental (E)
                e_scores.append(1 - sentimiento['pos'])  # Negativo = puntuación alta
            elif i in [1, 6]:  # Social (S)
                s_scores.append(sentimiento['pos'])  # Positivo = puntuación alta
            elif i in [2, 7]:  # Gobernanza (G)
                g_scores.append(1 - sentimiento['pos'])  # Negativo = puntuación alta
            elif i in [3, 4, 8]:  # Riesgo (R)
                r_scores.append(1 - sentimiento['pos'])  # Negativo = puntuación alta

        # Normalizar y redondear valores
        if e_scores:
            puntuaciones["Ambiental"] = round(max(0, min(100, (sum(e_scores) / len(e_scores)) * 100)))
        if s_scores:
            puntuaciones["Social"] = round(max(0, min(100, (sum(s_scores) / len(s_scores)) * 100)))
        if g_scores:
            puntuaciones["Gobernanza"] = round(max(0, min(100, (sum(g_scores) / len(g_scores)) * 100)))
        if r_scores:
            puntuaciones["Riesgo"] = round(max(0, min(100, (sum(r_scores) / len(r_scores)) * 100)))

    # Resto del código para mostrar y guardar resultados...


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
