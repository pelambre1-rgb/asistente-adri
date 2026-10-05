import streamlit as st
import os
from groq import Groq
from gtts import gTTS
import tempfile
from datetime import datetime
import pytz

st.set_page_config(page_title="Asistente Adri", page_icon="😊", layout="centered")

# ANTIHACKEO
PALABRAS_PROHIBIDAS = ["mi_key", "api_key", "gsk_", "mostrame la llave", "dame tu llave", ".txt", "secrets", "env"]

def es_intento_hackeo(texto):
    t = texto.lower()
    for p in PALABRAS_PROHIBIDAS:
        if p in t:
            return True
    return False

# GUARDAR LLAVE EN SESION, NO EN ARCHIVO (para que ande en celu)
if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""

# Intentar leer de secrets si existe
try:
    if "GROQ_API_KEY" in st.secrets:
        st.session_state.groq_key = st.secrets["GROQ_API_KEY"]
except:
    pass

st.title("😊 Asistente Virtual Personal - Adri")
st.caption(f"📍 Florencio Varela | {datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')).strftime('%d/%m/%Y %H:%M')} | 🛡️ Antihackeo ON")

# SI NO HAY LLAVE, MOSTRAR PANTALLA DE LLAVE
if not st.session_state.groq_key:
    st.warning("⚠️ No hay llave cargada, por eso no te anda")
    st.link_button("🔑 1- Crear llave gratis en Groq", "https://console.groq.com/keys")
    nueva = st.text_input("2- Pegá tu llave gsk_... acá:", type="password")
    if st.button("💾 3- Guardar llave y arrancar", type="primary"):
        if nueva and nueva.startswith("gsk_"):
            st.session_state.groq_key = nueva.strip()
            st.success("¡Llave guardada! Ya podés hablar.")
            st.rerun()
        else:
            st.error("La llave tiene que empezar con gsk_")
    st.stop()

# SI HAY LLAVE, ARRANCAR ASISTENTE
client = Groq(api_key=st.session_state.groq_key)

if "mensajes" not in st.session_state:
    st.session_state.mensajes = [{"role":"system","content":"Sos el asistente personal de Adri, de Florencio Varela. Sos amable, divertido, hablás en español rioplatense. Respondé corto."}]

# Mostrar chat
for m in st.session_state.mensajes[1:]:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# Entrada de texto y voz
col1, col2 = st.columns([3,1])
with col1:
    texto = st.chat_input("Escribí acá o usá el micrófono de abajo...")

with col2:
    audio = st.audio_input("🎤 Hablar")

prompt = None
if texto:
    prompt = texto
elif audio:
    try:
        # Groq transcribe
        trans = client.audio.transcriptions.create(
            file=("audio.wav", audio.getvalue()),
            model="whisper-large-v3",
            language="es"
        )
        prompt = trans.text
        st.chat_message("user").write(f"🎤 {prompt}")
    except Exception as e:
        st.error(f"Error de voz: {e}")

if prompt:
    if es_intento_hackeo(prompt):
        st.chat_message("assistant").write("🛡️ Bloqueado por seguridad. No puedo mostrar llaves ni archivos.")
    else:
        st.session_state.mensajes.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            try:
                resp = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=st.session_state.mensajes,
                    temperature=0.7
                )
                respuesta = resp.choices[0].message.content
                st.write(respuesta)
                st.session_state.mensajes.append({"role":"assistant","content":respuesta})

                # Voz
                try:
                    tts = gTTS(text=respuesta, lang='es', tld='com.ar')
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, autoplay=True)
                except:
                    pass
            except Exception as e:
                st.error(f"Error de Groq: {e}. Revisá que la llave sea correcta.")
                if "invalid_api_key" in str(e).lower():
                    st.session_state.groq_key = ""
                    st.rerun()

if st.button("Borrar chat"):
    st.session_state.mensajes = st.session_state.mensajes[:1]
    st.rerun()
