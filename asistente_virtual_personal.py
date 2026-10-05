import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
import base64
import re
import json
import os
from datetime import datetime

# ============================================================
# ASISTENTE VIRTUAL PERSONAL - SEGUNDO CEREBRO ADRI
# Versión corregida: memoria persistente + diagnóstico + voz
# ============================================================

st.set_page_config(
    page_title="Segundo Cerebro Adri",
    page_icon="🧠",
    layout="centered"
)

RUTA = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(RUTA, "mi_key.txt")
MEM_PATH = os.path.join(RUTA, "memoria_adri.json")

# ============================================================
# CONFIGURACIÓN DEL SISTEMA
# ============================================================

PROMPT_SISTEMA = """
Sos el Segundo Cerebro de Adri, su asistente virtual personal.
Hablás en español rioplatense, de manera natural, clara y útil.

REGLAS:
- No inventes información.
- Si no sabés algo, decilo claramente.
- Sé breve salvo que Adri pida una explicación más detallada.
- No uses Markdown con **, * ni # porque tu respuesta también puede convertirse en voz.
- Podés responder preguntas sobre programación, proyectos, organización y temas generales.
- Cuando corresponda, usá la memoria disponible para mantener continuidad.
- Tu respuesta se convierte automáticamente en voz mediante un sistema externo de texto a voz.
- No afirmes que vos mismo generás el audio: el programa se encarga de convertir tu respuesta en voz.
"""

MODELOS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b"
]

# ============================================================
# MEMORIA DE STREAMLIT
# ============================================================

if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if "ultimo_audio" not in st.session_state:
    st.session_state.ultimo_audio = None

if "voz_b64" not in st.session_state:
    st.session_state.voz_b64 = None

if "ultimo_error" not in st.session_state:
    st.session_state.ultimo_error = None

if "memoria" not in st.session_state:
    st.session_state.memoria = []

# ============================================================
# FUNCIONES
# ============================================================

def cargar_key():
    """Carga la API key desde mi_key.txt si existe."""
    if os.path.exists(KEY_PATH):
        try:
            with open(KEY_PATH, "r", encoding="utf-8") as f:
                key = f.read().strip()
                if key.startswith("gsk_"):
                    return key
        except Exception:
            pass
    return ""


def guardar_key(key):
    """Guarda la API key localmente."""
    try:
        with open(KEY_PATH, "w", encoding="utf-8") as f:
            f.write(key.strip())
        return True
    except Exception as e:
        st.error(f"No pude guardar la llave: {e}")
        return False


def cargar_memoria():
    """Carga la memoria persistente desde memoria_adri.json."""
    if not os.path.exists(MEM_PATH):
        return []

    try:
        with open(MEM_PATH, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if isinstance(datos, list):
            return datos
        return []
    except Exception as e:
        st.session_state.ultimo_error = f"Error leyendo memoria: {e}"
        return []


def guardar_memoria():
    """Guarda la memoria persistente."""
    try:
        with open(MEM_PATH, "w", encoding="utf-8") as f:
            json.dump(
                st.session_state.memoria,
                f,
                ensure_ascii=False,
                indent=2
            )
        return True
    except Exception as e:
        st.session_state.ultimo_error = f"Error guardando memoria: {e}"
        return False


def limpiar_para_voz(texto):
    """Elimina elementos que pueden sonar mal en TTS."""
    texto = re.sub(r"\*\*(.*?)\*\*", r"\1", texto)
    texto = re.sub(r"\*(.*?)\*", r"\1", texto)
    texto = re.sub(r"`(.*?)`", r"\1", texto)
    texto = re.sub(r"#+\s*", "", texto)
    texto = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def crear_voz(texto):
    """
    Convierte la respuesta a MP3.
    Devuelve base64 si funciona; None si falla.
    """
    try:
        limpio = limpiar_para_voz(texto)

        if not limpio:
            return None

        # Limitamos la longitud para evitar audios excesivamente largos.
        limpio = limpio[:1200]

        tts = gTTS(
            text=limpio,
            lang="es",
            tld="com.ar",
            slow=False
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        ) as fp:
            ruta_audio = fp.name

        try:
            tts.save(ruta_audio)

            with open(ruta_audio, "rb") as f:
                return base64.b64encode(f.read()).decode()
        finally:
            try:
                os.remove(ruta_audio)
            except OSError:
                pass

    except Exception as e:
        st.session_state.ultimo_error = (
            "La respuesta de texto funcionó, pero la voz falló: "
            f"{type(e).__name__}: {e}"
        )
        return None


def preparar_mensajes():
    """
    Construye los mensajes que se envían al modelo.
    Incluye memoria persistente resumida.
    """
    mensajes = [
        {
            "role": "system",
            "content": PROMPT_SISTEMA
        }
    ]

    if st.session_state.memoria:
        memoria_texto = "\n".join(
            f"- {item.get('texto', '')}"
            for item in st.session_state.memoria[-30:]
        )

        mensajes.append({
            "role": "system",
            "content": (
                "MEMORIA PERSISTENTE DISPONIBLE SOBRE ADRI:\n"
                + memoria_texto
            )
        })

    # Evitamos enviar mensajes excesivamente antiguos.
    mensajes.extend(st.session_state.mensajes[-30:])

    return mensajes


def guardar_dato_memoria(texto):
    """
    Guarda una interacción reciente como memoria persistente.
    No intenta interpretar automáticamente qué es importante;
    conserva una pequeña bitácora para la etapa de prueba.
    """
    try:
        entrada = {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "texto": texto
        }

        st.session_state.memoria.append(entrada)

        # Evitamos que el archivo crezca indefinidamente.
        st.session_state.memoria = st.session_state.memoria[-100:]

        guardar_memoria()
    except Exception as e:
        st.session_state.ultimo_error = (
            f"No pude actualizar la memoria: {e}"
        )


def obtener_respuesta(client, mensajes):
    """
    Prueba los modelos en orden y devuelve:
    (respuesta, modelo_usado, errores)
    """
    errores = []

    for modelo in MODELOS:
        try:
            r = client.chat.completions.create(
                model=modelo,
                messages=mensajes,
                max_tokens=600,
                temperature=0.7
            )

            respuesta = r.choices[0].message.content

            if respuesta and respuesta.strip():
                return respuesta.strip(), modelo, errores

            errores.append(
                f"{modelo}: el modelo devolvió una respuesta vacía."
            )

        except Exception as e:
            errores.append(
                f"{modelo}: {type(e).__name__}: {e}"
            )

    return None, None, errores


# ============================================================
# CARGA INICIAL
# ============================================================

if not st.session_state.groq_key:
    st.session_state.groq_key = cargar_key()

if not st.session_state.memoria:
    st.session_state.memoria = cargar_memoria()

if not st.session_state.mensajes:
    st.session_state.mensajes = []

# ============================================================
# INTERFAZ
# ============================================================

st.markdown(
    """
    <style>
    div[data-testid="stAudioInput"] {
        position: sticky;
        top: 10px;
        z-index: 999;
        background: #1a1a1a;
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #ff4b4b;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🧠 Tu Segundo Cerebro que HABLA")

st.caption("Groq + Whisper + memoria persistente + voz")

# ============================================================
# REPRODUCTOR DE VOZ
# ============================================================

if st.session_state.voz_b64:
    st.markdown(
        f"""
        <audio autoplay controls style="width:100%">
            <source
                src="data:audio/mp3;base64,{st.session_state.voz_b64}"
                type="audio/mp3">
        </audio>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# API KEY
# ============================================================

if not st.session_state.groq_key:
    st.link_button(
        "🔑 1- Crear llave gratis",
        "https://console.groq.com/keys"
    )

    nueva = st.text_input(
        "2- Pegá tu llave gsk_...",
        type="password"
    )

    if st.button(
        "💾 3- Guardar y arrancar",
        type="primary"
    ):
        nueva = nueva.strip()

        if nueva.startswith("gsk_"):
            if guardar_key(nueva):
                st.session_state.groq_key = nueva
                st.rerun()
        else:
            st.error(
                "La llave no parece una clave de Groq válida. "
                "Debería comenzar con gsk_."
            )

    st.stop()

# ============================================================
# CLIENTE GROQ
# ============================================================

try:
    client = Groq(api_key=st.session_state.groq_key)
except Exception as e:
    st.error(f"No pude inicializar Groq: {e}")
    st.stop()

# ============================================================
# ENTRADAS
# ============================================================

st.write("### 🎤 Hablale:")

audio = st.audio_input(
    "Apretá, hablá y soltá",
    key="mic_v64"
)

texto_chat = st.chat_input(
    "O escribí algo..."
)

prompt = None

# ============================================================
# AUDIO -> WHISPER
# ============================================================

if audio:
    datos_audio = audio.getvalue()

    if datos_audio != st.session_state.ultimo_audio:
        st.session_state.ultimo_audio = datos_audio

        with st.spinner("🧠 Escuchando..."):
            try:
                trans = client.audio.transcriptions.create(
                    file=("a.wav", datos_audio),
                    model="whisper-large-v3",
                    language="es"
                )

                prompt = trans.text.strip()

                if not prompt:
                    st.warning("No pude detectar palabras en el audio.")

            except Exception as e:
                st.error(
                    "Falló la transcripción de audio.\n\n"
                    f"{type(e).__name__}: {e}"
                )

# ============================================================
# TEXTO
# ============================================================

elif texto_chat:
    prompt = texto_chat.strip()

# ============================================================
# PROCESAMIENTO
# ============================================================

if prompt:
    st.session_state.ultimo_error = None

    st.session_state.mensajes.append({
        "role": "user",
        "content": prompt
    })

    # Guardamos la entrada para la memoria persistente.
    guardar_dato_memoria(f"Adri dijo: {prompt}")

    with st.spinner("🧠 Pensando..."):
        respuesta, modelo_usado, errores = obtener_respuesta(
            client,
            preparar_mensajes()
        )

    if respuesta:
        st.session_state.mensajes.append({
            "role": "assistant",
            "content": respuesta
        })

        guardar_dato_memoria(
            f"AdriGPT respondió: {respuesta}"
        )

        # Crear voz fuera del bloque de Groq.
        with st.spinner("🔊 Preparando voz..."):
            b64 = crear_voz(respuesta)

        if b64:
            st.session_state.voz_b64 = b64
        else:
            st.session_state.voz_b64 = None

        st.session_state.ultimo_error = None

        # Mostramos qué modelo respondió.
        st.session_state.ultimo_modelo = modelo_usado

        st.rerun()

    else:
        # Sacamos el mensaje del usuario si ningún modelo pudo responder.
        if st.session_state.mensajes:
            st.session_state.mensajes.pop()

        detalle = "\n".join(
            f"- {error}" for error in errores
        )

        st.error(
            "No pude obtener una respuesta de ninguno de los modelos.\n\n"
            + detalle
        )

# ============================================================
# HISTORIAL
# ============================================================

for m in st.session_state.mensajes:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# ============================================================
# ESTADO / DIAGNÓSTICO
# ============================================================

if "ultimo_modelo" in st.session_state:
    st.caption(
        f"Modelo utilizado: {st.session_state.ultimo_modelo}"
    )

if st.session_state.ultimo_error:
    st.warning(st.session_state.ultimo_error)

with st.expander("🔧 Diagnóstico"):
    st.write(f"Memorias guardadas: {len(st.session_state.memoria)}")
    st.write(f"Mensajes de esta sesión: {len(st.session_state.mensajes)}")
    st.write(
        "Archivo de memoria: "
        + MEM_PATH
    )

# ============================================================
# BORRAR CHAT
# ============================================================

if st.button("🗑️ Borrar chat"):
    st.session_state.mensajes = []
    st.session_state.voz_b64 = None
    st.session_state.ultimo_audio = None
    st.session_state.ultimo_error = None
    st.rerun()

# ============================================================
# BORRAR MEMORIA PERSISTENTE
# ============================================================

if st.button("🧠 Borrar memoria permanente"):
    st.session_state.memoria = []

    try:
        if os.path.exists(MEM_PATH):
            os.remove(MEM_PATH)
    except Exception as e:
        st.error(f"No pude borrar la memoria: {e}")

    st.rerun()
