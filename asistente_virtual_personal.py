import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import base64
from datetime import datetime
import pytz

st.set_page_config(page_title="Asistente Adri", page_icon="🧠", layout="centered")

if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [{"role":"system","content":"Sos el segundo cerebro de Adri de Florencio Varela. Hablás rioplatense, corto, amable, como un amigo. Respondé siempre hablando, como conversación real."}]
if "ultimo_audio" not in st.session_state:
    st.session_state.ultimo_audio = None

def hablar_auto(texto):
    try:
        tts = gTTS(text=texto[:400], lang='es', tld='com.ar', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            with open(fp.name, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                # Este truco hace que hable solo, sin que apretes play
                audio_html = f'<audio autoplay controls style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
                st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error voz: {e}")

st.title("🧠 Tu Segundo Cerebro - Adri")
st.caption(f"📍 Varela | {datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')).strftime('%H:%M')} | Habla automático ON")

# --- LLAVE ---
if not st.session_state.groq_key:
    st.link_button("🔑 1- Crear llave gratis", "https://console.groq.com/keys")
    nueva = st.text_input("2- Pegá tu llave gsk_... acá:", type="password")
    if st.button("💾 3- Guardar y arrancar", type="primary"):
        if nueva.startswith("gsk_"):
            st.session_state.groq_key = nueva.strip()
            st.rerun()
    st.stop()

client = Groq(api_key=st.session_state.groq_key)

# --- CHAT ---
for m in st.session_state.mensajes[1:]:
    with st.chat_message(m["role"]):
        st.write(m["content"])

st.divider()
st.write("🎤 **HABLALE ACÁ ABAJO - Es tu segundo cerebro:**")
audio = st.audio_input("Apretá, hablá y soltá. Te responde solo.", key="mic_cerebro")

prompt = None
if audio and audio.getvalue()!= st.session_state.ultimo_audio:
    st.session_state.ultimo_audio = audio.getvalue()
    with st.spinner("🧠 Escuchando y pensando..."):
        try:
            trans = client.audio.transcriptions.create(
                file=("audio.wav", audio.getvalue()),
                model="whisper-large-v3",
                language="es"
            )
            prompt = trans.text
            st.chat_message("user").write(f"🎤 Vos: {prompt}")
        except Exception as e:
            st.error(f"No te escuché: {e}")

# Texto también por si querés escribir
texto_chat = st.chat_input("O escribí acá si querés...")
if texto_chat:
    prompt = texto_chat
    with st.chat_message("user"):
        st.write(prompt)

if prompt:
    st.session_state.mensajes.append({"role":"user","content":prompt})
    with st.chat_message("assistant"):
        with st.spinner("..."):
            respuesta = None
            for modelo in ["llama-3.3-70b-versatile", "openai/gpt-oss-20b", "qwen/qwen3-32b", "gemma2-9b-it"]:
                try:
                    r = client.chat.completions.create(
                        model=modelo,
                        messages=st.session_state.mensajes,
                        max_tokens=500,
                        temperature=0.7
                    )
                    respuesta = r.choices[0].message.content
                    break
                except:
                    continue

            if respuesta:
                st.write(respuesta)
                st.session_state.mensajes.append({"role":"assistant","content":respuesta})
                hablar_auto(respuesta) # ACA ESTA LA MAGIA, HABLA SOLO
            else:
                st.error("Groq no respondió, probá de nuevo")

if st.button("🗑️ Borrar memoria"):
    st.session_state.mensajes = [st.session_state.mensajes[0]]
    st.session_state.ultimo_audio = None
    st.rerun()
