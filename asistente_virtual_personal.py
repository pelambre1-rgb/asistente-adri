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
    st.session_state.mensajes = [{"role":"system","content":"Sos el segundo cerebro de Adri de Florencio Varela. Sos su asistente personal que habla. Respondé siempre como si hablaras, corto, rioplatense, amable, con memoria. Sos su amigo que lo ayuda con todo."}]
if "ultimo_audio" not in st.session_state:
    st.session_state.ultimo_audio = None
if "abrir_url" not in st.session_state:
    st.session_state.abrir_url = None

def hablar_por_voz(texto):
    try:
        tts = gTTS(text=texto[:400], lang='es', tld='com.ar', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            with open(fp.name, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                # Esto hace que HABLE SOLO sin apretar play
                st.markdown(f'<audio autoplay controls><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    except:
        pass

def detectar_red(texto):
    t = texto.lower()
    redes = {"instagram":"https://www.instagram.com","facebook":"https://www.facebook.com","youtube":"https://www.youtube.com","tiktok":"https://www.tiktok.com","whatsapp":"https://web.whatsapp.com"}
    for n,u in redes.items():
        if n in t and ("abri" in t or "abrir" in t):
            return n,u
    return None,None

# MICROFONO FIJO ARRIBA - NO SE VA MAS
st.markdown("""
<style>
div[data-testid="stAudioInput"] {position: sticky; top: 10px; z-index: 999; background: #1a1a1a; padding: 15px; border-radius: 15px; border: 2px solid #ff4b4b;}
</style>
""", unsafe_allow_html=True)

st.title("🧠 Tu Segundo Cerebro que HABLA")

# --- LLAVE ---
if not st.session_state.groq_key:
    st.link_button("🔑 1- Crear llave gratis", "https://console.groq.com/keys")
    nueva = st.text_input("2- Pegá tu llave gsk_...", type="password")
    if st.button("💾 3- Guardar y arrancar", type="primary"):
        if nueva.startswith("gsk_"):
            st.session_state.groq_key = nueva.strip()
            st.rerun()
    st.stop()

client = Groq(api_key=st.session_state.groq_key)

# ABRIR REDES
if st.session_state.abrir_url:
    url = st.session_state.abrir_url
    st.link_button(f"👉 ABRIR {st.session_state.abrir_nombre.upper()}", url, type="primary", use_container_width=True)
    components.html(f'<script>window.open("{url}", "_blank")</script>', height=0)
    if st.button("Volver"):
        st.session_state.abrir_url = None
        st.rerun()
    st.stop()

# --- ACA ESTA LO QUE QUERES: MICRO ARRIBA Y QUE TE HABLE ---
st.write("### 🎤 Preguntale, te responde hablando:")
audio = st.audio_input("Apretá, preguntá y soltá. Te responde por voz.", key="mic_cerebro_habla")

texto_chat = st.chat_input("O escribí acá...")

prompt = None
if audio and audio.getvalue()!= st.session_state.ultimo_audio:
    st.session_state.ultimo_audio = audio.getvalue()
    with st.spinner("🧠 Escuchando..."):
        try:
            trans = client.audio.transcriptions.create(file=("a.wav", audio.getvalue()), model="whisper-large-v3", language="es")
            prompt = trans.text
            st.write(f"🎤 Vos dijiste: **{prompt}**")
        except Exception as e:
            st.error(f"No te escuché: {e}")
elif texto_chat:
    prompt = texto_chat

if prompt:
    red_n, red_u = detectar_red(prompt)
    if red_u:
        st.session_state.abrir_url = red_u
        st.session_state.abrir_nombre = red_n
        hablar_por_voz(f"Dale Adri, abriendo {red_n}")
        st.rerun()
    else:
        st.session_state.mensajes.append({"role":"user","content":prompt})
        with st.spinner("🧠 Pensando y hablando..."):
            respuesta = None
            for modelo in ["llama-3.3-70b-versatile","openai/gpt-oss-20b","qwen/qwen3-32b"]:
                try:
                    r = client.chat.completions.create(model=modelo, messages=st.session_state.mensajes, max_tokens=500)
                    respuesta = r.choices[0].message.content
                    break
                except:
                    continue
            if respuesta:
                st.session_state.mensajes.append({"role":"assistant","content":respuesta})
                st.chat_message("assistant").write(respuesta)
                hablar_por_voz(respuesta) # <--- ACA TE HABLA POR VOZ DIRECTO

# Historial abajo
st.divider()
for m in st.session_state.mensajes[1:]:
    with st.chat_message(m["role"]):
        st.write(m["content"])
