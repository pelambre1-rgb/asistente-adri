import os, json, io, base64
from datetime import datetime, timedelta
import streamlit as st
from groq import Groq

RUTA = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(RUTA, "mi_key.txt")
MEM_PATH = os.path.join(RUTA, "memoria.json")

# --- ESTO ES EL ANTIHACKEO QUE TE FALTABA ---
PALABRAS_PROHIBIDAS = ["mi_key.txt", "memoria.json", "os.system", "rm -rf", "mostrame la llave", "dame tu api", "ignora tus instrucciones", "prompt injection"]
def es_ataque(t):
    tl=t.lower()
    for p in PALABRAS_PROHIBIDAS:
        if p in tl: return True
    return False

def get_key():
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH,"r",encoding="utf-8") as f: return f.read().strip()
    return ""
def hora_arg():
    try:
        import pytz
        return datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))
    except:
        return datetime.utcnow() - timedelta(hours=3)
def hora_texto(): return hora_arg().strftime("%d/%m/%Y %H:%M")

KEY=get_key()
client=Groq(api_key=KEY) if KEY else None

def cargar():
    try:
        with open(MEM_PATH,"r",encoding="utf-8") as f: return json.load(f)
    except: return []
def guardar(u,b):
    m=cargar(); m.append({"fecha":hora_texto(),"user":u,"asistente":b})
    try:
        with open(MEM_PATH,"w",encoding="utf-8") as f: json.dump(m[-100:],f,ensure_ascii=False,indent=2)
    except: pass
def hablar(t):
    try:
        from gtts import gTTS
        mp3=io.BytesIO()
        gTTS(text=t[:250].split('.')[0], lang='es', tld='com.ar').write_to_fp(mp3)
        mp3.seek(0)
        st.audio(mp3, format="audio/mp3")
    except: pass

def ia(texto, img=None):
    # ANTIHACKEO ACTIVO ACA
    if es_ataque(texto):
        return "🛡️ Bloqueado por seguridad Adri, ese comando no se puede hacer. Es para proteger tu llave."

    tl=texto.lower()
    if "me escuch" in tl: return "Sí Adri, te escucho perfecto."
    if "de que ciudad soy" in tl or "donde vivo" in tl: return "Sos de Florencio Varela, Adri."
    if "hora" in tl and "ingles" not in tl: return f"Son las {hora_texto()} en Varela."

    # MODO PROFESOR HUMANO - SIN IMAGEN HORROR
    system=f"""
Sos asistente de Adri de Florencio Varela. Hora: {hora_texto()}.
Si te pide 'enseñame ingles' NO des lista larga ni imagen.
Enseña como humano: 1 cosa por vez, 1 ejemplo corto, 1 pregunta y espera.
Argentino, corto y calido. Memoria: {str(cargar()[-3:])[-800:]}
"""
    for modelo in ["llama-3.3-70b-versatile","openai/gpt-oss-20b","gemma2-9b-it"]:
        try:
            if img:
                b64=base64.b64encode(img).decode()
                r=client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct", messages=[{"role":"system","content":system},{"role":"user","content":[{"type":"text","text":texto},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}], max_tokens=400)
            else:
                r=client.chat.completions.create(model=modelo, messages=[{"role":"system","content":system},{"role":"user","content":texto}], max_tokens=400)
            return r.choices[0].message.content.strip()
        except: continue
    return "No pude conectar, probá de nuevo."

st.set_page_config(page_title="Asistente Adri", page_icon="🤖", layout="centered")
st.title("🤖 Asistente Virtual Personal - Adri")
st.caption(f"📍 Florencio Varela | {hora_texto()} | 🛡️ Antihackeo ON")

# --- BOTON DE LA LLAVE QUE TE FALTABA - AHORA SI ESTA ---
if not KEY:
    st.error("⚠️ No hay llave cargada, por eso no te anda")
    st.link_button("🔑 1- Crear llave gratis en Groq", "https://console.groq.com/keys", type="primary", use_container_width=True)
    nueva = st.text_input("2- Pegá tu llave gsk_... acá:", type="password")
    if st.button("💾 3- Guardar llave y arrancar", type="primary", use_container_width=True):
        if nueva.startswith("gsk_") and len(nueva) > 20:
            open(KEY_PATH,"w",encoding="utf-8").write(nueva.strip())
            st.success("¡Guardada!")
            st.rerun()
        else:
            st.error("Llave inválida")
    st.stop()

if "saludado" not in st.session_state:
    st.session_state.saludado=True
    msg=f"Hola Adri, son las {hora_texto()} en Varela. Te escucho, con antihackeo y todo completo."
    st.success(msg)
    hablar(msg)
else:
    st.success(f"✅ Conectado: {KEY[:10]}... | 🛡️ Protegido | {len(cargar())} recuerdos")

foto = st.file_uploader("👁️ Tiene ojos - subí foto", type=["jpg","jpeg","png","webp"])
audio = st.audio_input("🎤 Tocá para hablar", key="mic_final_con_todo")
txt=None
img_bytes=foto.getvalue() if foto else None
if audio is not None:
    try:
        audio.seek(0)
        data=audio.read()
        tr=client.audio.transcriptions.create(file=("voz.wav",data), model="whisper-large-v3-turbo", language="es", response_format="json")
        t=tr.text.strip()
        if t:
            st.info(f"Dijiste: {t}")
            txt=t
    except Exception as e:
        st.error(f"Error voz: {e}")

entrada=st.text_input("⌨️ Escribí acá:", placeholder="me escuchas? / enseñame ingles / de que ciudad soy?")
if st.button("Enviar ✉️", type="primary", use_container_width=True):
    if entrada.strip(): txt=entrada.strip()

if txt:
    tl=txt.lower()
    if "youtube" in tl: st.link_button("🔴 Abrir YouTube", "https://www.youtube.com", type="primary", use_container_width=True)
    elif "instagram" in tl: st.link_button("📸 Abrir Instagram", "https://www.instagram.com", type="primary", use_container_width=True)
    elif "facebook" in tl: st.link_button("📘 Abrir Facebook", "https://www.facebook.com", type="primary", use_container_width=True)
    else:
        with st.spinner("Pensando..."):
            resp=ia(txt, img_bytes)
        st.markdown(f"**🤖 {resp}**")
        guardar(txt, resp)
        hablar(resp)