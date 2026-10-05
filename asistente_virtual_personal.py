import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import base64
from datetime import datetime
import pytz
import streamlit.components.v1 as components

st.set_page_config(page_title="Segundo Cerebro Adri", page_icon="🧠", layout="centered")

if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [{"role":"system","content":"Sos el segundo cerebro de Adri de Florencio Varela. Vos sos AdriGPT, un asistente que HABLA. REGLA DE ORO: Nunca digas que no podes generar audio, ni que sos solo texto, ni que no tenes motor de voz. El sistema externo SI genera tu voz con gTTS automaticamente. Vos solo tenes que responder el contenido util, corto y rioplatense. Si te preguntan por que no generas audio, respondé: 'Si genero audio Adri, me escuchas arriba en el reproductor, el sistema me pone voz argentina automaticamente'. Nunca uses ** ni * ni #. Ejemplo de ingles: hello (hola)."}]
if "ultimo_audio" not in st.session_state:
    st.session_state.ultimo_audio = None
if "voz_b64" not in st.session_state:
    st.session_state.voz_b64 = None
if "abrir_url" not in st.session_state:
    st.session_state.abrir_url = None

def crear_voz(texto):
    try:
        tts = gTTS(text=texto[:400], lang='es', tld='com.ar', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            with open(fp.name, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        return None
def limpiar_para_voz(texto):
    import re
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    texto = texto.replace('**','').replace('*','').replace('#','').replace('`','')
    return texto
# Microfono fijo arriba
st.markdown("""
<style>
div[data-testid="stAudioInput"] {position: sticky; top: 10px; z-index: 999; background: #1a1a1a; padding: 15px; border-radius: 15px; border: 2px solid #ff4b4b;}
</style>
""", unsafe_allow_html=True)

st.title("🧠 Tu Segundo Cerebro que HABLA SIEMPRE")

# --- ESTO ES LO QUE FALTABA: REPRODUCE LA ULTIMA VOZ SIEMPRE ARRIBA ---
if st.session_state.voz_b64:
    st.markdown(f'<audio autoplay controls style="width:100%"><source src="data:audio/mp3;base64,{st.session_state.voz_b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)

if not st.session_state.groq_key:
    st.link_button("🔑 1- Crear llave gratis", "https://console.groq.com/keys")
    nueva = st.text_input("2- Pegá tu llave gsk_...", type="password")
    if st.button("💾 3- Guardar y arrancar", type="primary"):
        if nueva.startswith("gsk_"):
            st.session_state.groq_key = nueva.strip()
            st.rerun()
    st.stop()

client = Groq(api_key=st.session_state.groq_key)

if st.session_state.abrir_url:
    url = st.session_state.abrir_url
    st.link_button(f"👉 ABRIR {st.session_state.abrir_nombre.upper()}", url, type="primary", use_container_width=True)
    components.html(f'<script>window.open("{url}", "_blank")</script>', height=0)
    if st.button("Volver"):
        st.session_state.abrir_url = None
        st.rerun()
    st.stop()

st.write("### 🎤 Hablale, te responde hablando siempre:")
audio = st.audio_input("Apretá, hablá y soltá", key="mic_fijo")
texto_chat = st.chat_input("O escribí 'enseñame inglés'...")

prompt = None
if audio and audio.getvalue()!= st.session_state.ultimo_audio:
    st.session_state.ultimo_audio = audio.getvalue()
    with st.spinner("🧠 Escuchando..."):
        try:
            trans = client.audio.transcriptions.create(file=("a.wav", audio.getvalue()), model="whisper-large-v3", language="es")
            prompt = trans.text
        except Exception as e:
            st.error(f"Error: {e}")
elif texto_chat:
    prompt = texto_chat

if prompt:
    st.session_state.mensajes.append({"role":"user","content":prompt})
    with st.spinner("🧠 Respondiendo con voz..."):
        respuesta = None
        for modelo in ["llama-3.3-70b-versatile","openai/gpt-oss-20b","qwen/qwen3-32b"]:
            try:
                r = client.chat.completions.create(model=modelo, messages=st.session_state.mensajes, max_tokens=600, temperature=0.7)
                respuesta = r.choices[0].message.content
                break
            except:
                continue
        if respuesta:
            st.session_state.mensajes.append({"role":"assistant","content":respuesta})
            b64 = crear_voz(respuesta)
            if b64:
                st.session_state.voz_b64 = b64
            st.rerun()

# Historial
for m in st.session_state.mensajes[1:]:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if st.button("🗑️ Borrar chat"):
    st.session_state.mensajes = [st.session_state.mensajes[0]]
    st.session_state.voz_b64 = None
    st.rerun()
