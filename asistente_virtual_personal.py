import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import base64
import re
import streamlit.components.v1 as components

st.set_page_config(page_title="Segundo Cerebro Adri", page_icon="🧠", layout="centered")

# --- MEMORIA ---
if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "ultimo_audio" not in st.session_state:
    st.session_state.ultimo_audio = None
if "voz_b64" not in st.session_state:
    st.session_state.voz_b64 = None

# FORZAMOS EL CEREBRO NUEVO SIEMPRE - ACÁ ESTABA EL BUG
PROMPT_SISTEMA = "Sos el segundo cerebro de Adri de Florencio Varela. Sos AdriGPT y VOS SI HABLAS. REGLA DE ORO: NUNCA digas que no podes generar audio, nunca digas que sos solo texto, nunca digas que no tenes motor de voz. El sistema externo te da voz argentina con gTTS automaticamente. Si te preguntan 'por que no podes generar audio', responde: 'Si puedo Adri, me escuchas arriba en el reproductor, tengo voz'. Hablas rioplatense, corto, util. Nunca uses ** ni * ni #. Para ingles deci: hello (hola)."

# Si la memoria esta vacia o tiene el prompt viejo, lo pisamos
if len(st.session_state.mensajes) == 0 or "arquitectura" in str(st.session_state.mensajes[0]):
    st.session_state.mensajes = [{"role":"system","content":PROMPT_SISTEMA}]
else:
    # Actualizamos siempre el system para que no vuelva la excusa
    st.session_state.mensajes[0] = {"role":"system","content":PROMPT_SISTEMA}

def limpiar_para_voz(texto):
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    texto = re.sub(r'\*(.*?)\*', r'\1', texto)
    return texto.replace('**','').replace('*','').replace('#','').replace('`','')

def crear_voz(texto):
    try:
        limpio = limpiar_para_voz(texto)[:450]
        tts = gTTS(text=limpio, lang='es', tld='com.ar', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            with open(fp.name, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        return None

st.markdown("""<style>div[data-testid="stAudioInput"] {position: sticky; top: 10px; z-index: 999; background: #1a1a1a; padding: 15px; border-radius: 15px; border: 2px solid #ff4b4b;}</style>""", unsafe_allow_html=True)
st.title("🧠 Tu Segundo Cerebro que HABLA")

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

st.write("### 🎤 Hablale:")
audio = st.audio_input("Apretá, hablá y soltá", key="mic_v63_final")
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

for m in st.session_state.mensajes[1:]:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if st.button("🗑️ Borrar chat"):
    st.session_state.mensajes = [{"role":"system","content":PROMPT_SISTEMA}]
    st.session_state.voz_b64 = None
    st.rerun()
