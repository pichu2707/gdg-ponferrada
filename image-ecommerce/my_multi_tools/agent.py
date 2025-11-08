import os
from dotenv import load_dotenv
load_dotenv(override=True)

# Forzar modo API (Gemini API, no Vertex AI para el agente)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"

# Configurar credenciales para Veo (que SÍ usa Vertex AI)
proj = os.getenv("GCP_PROJECT_ID") or "gdg-ponferrada"
loc = os.getenv("GCP_LOCATION") or "us-central1"
os.environ["GOOGLE_CLOUD_PROJECT"] = proj
os.environ["GOOGLE_CLOUD_LOCATION"] = loc

CRED_ENV = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
upper_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "gcp-credentials.json"
)
if not CRED_ENV or not os.path.isfile(CRED_ENV):
    if os.path.isfile(upper_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = upper_path
        print(f"[FIX] GOOGLE_APPLICATION_CREDENTIALS -> {upper_path}")

print(f"[DEBUG] Gemini API mode | GCP Project={proj}, Location={loc}")


import datetime
import time 
import mimetypes 
from typing import List, Dict, Union
from google.adk.agents.llm_agent import Agent
# Importamos la clase del otro archivo
from .wordpress_downloader import WordPressMediaDownload 
from .veo_images_videos import (
    generate_videos_for_list, 
    generate_videos_in_folder
    )

# Importaciones reales para la API de Veo (GenAI SDK)
from google import genai
from google.genai import types


# Forzar uso de Vertex AI y proporcionar project/location para google-genai
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")

proj = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "gdg-ponferrada"
loc = os.getenv("GCP_LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"

os.environ["GOOGLE_CLOUD_PROJECT"] = proj
os.environ["GOOGLE_CLOUD_LOCATION"] = loc
# Algunas versiones del SDK también leen estas:
os.environ["GOOGLE_GENAI_PROJECT"] = proj
os.environ["GOOGLE_GENAI_LOCATION"] = loc

# Resolver GOOGLE_APPLICATION_CREDENTIALS (fallback al JSON en image-ecommerce)
CRED_ENV = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
upper_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "gcp-credentials.json"
)
if not CRED_ENV or not os.path.isfile(CRED_ENV):
    if os.path.isfile(upper_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = upper_path
        print(f"[FIX] GOOGLE_APPLICATION_CREDENTIALS -> {upper_path}")
    else:
        raise FileNotFoundError(f"Credenciales no encontradas: {CRED_ENV or '(vacío)'} ni {upper_path}")

print(f"[DEBUG] GOOGLE_APPLICATION_CREDENTIALS={os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
print(f"[DEBUG] GOOGLE_CLOUD_PROJECT={os.getenv('GOOGLE_CLOUD_PROJECT')}, GOOGLE_CLOUD_LOCATION={os.getenv('GOOGLE_CLOUD_LOCATION')}")


# ----------------------------------------------------------------------
# Funciones auxiliares para el cliente de Veo
# ----------------------------------------------------------------------


# def _get_veo_client():
#     """Inicializa y devuelve el cliente de genai (Vertex AI) para Veo."""
#     try:
#         # Usando la nueva SDK de Google GenAI
#         client = genai.Client(
#             vertexai=True,
#             project=os.getenv("GCP_PROJECT_ID", "gdg-ponferrada"),
#             location=os.getenv("GCP_LOCATION", "us-central1"),
#         )
#         print(f"[X] Cliente GCP inicializado (GenAI SDK) para Veo.")
#         return client
#     except Exception as e:
#         print(f"Error al inicializar el cliente de Vertex AI (GenAI): {e}")
#         return None

# def _guess_mime_type(path: str) -> str:
#     """Obtiene un MIME type robusto basado en mimetypes/extensión."""
#     mimetypes.add_type('image/webp', '.webp') 
#     mime, _ = mimetypes.guess_type(path)
#     if mime:
#         return mime
#     ext = os.path.splitext(path)[1].lower()
#     return {
#         '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
#         '.gif': 'image/gif', '.webp': 'image/webp',
#     }.get(ext, 'image/jpeg')


# ----------------------------------------------------------------------
# 1. HERRAMIENTA DE EXTRACCIÓN (Wrapper para la clase WordPress)
# ----------------------------------------------------------------------

def extraer_imagenes_de_cms(cms_url: str, cms_platform: str) -> Dict[str, Union[str, List[str]]]:
    """
    Extrae imágenes desde la librería de medios de un CMS específico (WordPress, Shopify, etc.).

    Args:
        cms_url: La URL base del sitio web del CMS (ej: 'https://misitio.com').
        cms_platform: La plataforma CMS a la que conectarse (actualmente solo soporta 'wordpress').

    Returns:
        Un diccionario con 'status' y la lista de 'rutas_archivos_locales' o un 'error_message'.
    """
    if cms_platform.lower() == "wordpress":
        try:
            # Crea una instancia de tu clase y la ejecuta
            downloader = WordPressMediaDownload(cms_url)
            local_paths = downloader.run(destination_folder=f'images/{cms_platform.lower()}')
            
            if local_paths:
                return {
                    "status": "success",
                    "rutas_archivos_locales": local_paths,
                    "message": f"Descargadas {len(local_paths)} imágenes de WordPress. Usa una de estas rutas para generar el video."
                }
            else:
                return {
                    "status": "warning",
                    "rutas_archivos_locales": [],
                    "message": "Conexión exitosa, pero no se encontraron imágenes de producto después de aplicar los filtros."
                }
        except ValueError as e:
            return {"status": "error", "error_message": f"Error de URL o conexión: {e}"}
        except Exception as e:
            return {"status": "error", "error_message": f"Fallo al ejecutar WordPress Downloader: {e}"}
    
    # Lógica de escalabilidad futura
    elif cms_platform.lower() == "shopify":
        # TODO: Implementar la lógica para la API de Shopify aquí
        return {"status": "error", "error_message": "El soporte para Shopify está en desarrollo."}
    
    else:
        return {"status": "error", "error_message": f"Plataforma CMS no soportada: {cms_platform}."}


# ----------------------------------------------------------------------
# 2. HERRAMIENTA DE GENERACIÓN DE VIDEO (Veo) - LÓGICA INTEGRADA DEL SCRIPT
# ----------------------------------------------------------------------

def generar_video_veo(ruta_imagen_origen: str, prompt_video: str, duracion_segundos: int = 8) -> Dict[str, str]:
    """
    Genera un video promocional usando el modelo Veo (veo-2.0-generate-001) 
    a partir de una imagen y un prompt detallado, integrando tu lógica de polling.

    Args:
        ruta_imagen_origen: Ruta local del archivo de imagen (ej: 'images/wp/vestido-1.webp').
        prompt_video: El prompt descriptivo del video (ej: 'Vestido fluyendo con luz suave').
        duracion_segundos: La duración deseada del video. Por defecto es 8 segundos.

    Returns:
        Un diccionario con 'status' y 'video_path' o un 'error_message'.
    """
    
    if not os.path.exists(ruta_imagen_origen):
        return {
            "status": "error", 
            "error_message": f"Error: La imagen de origen no existe en la ruta: {ruta_imagen_origen}"
            }
    
    prompt = f"{prompt_video}. Short {duracion_segundos} seconds.  cinematic shot, smooth camera, natural motion."
    res = generate_videos_for_list(
        [ruta_imagen_origen],
        prompt=prompt,
    )
    item = res.get("results", [{}])[0]
    if item.get("video_path"):
        return {
            "status": "success",
            "video_path": item["video_path"],
            "message": f"Video de {duracion_segundos}s generado con éxito por Veo."
        }
    return {
        "status": "error",
        "error_message": item.get("error_message", "Fallo desconocido en la generación de video de Veo.")
    }


def generar_videos_desde_archivos(
        nombre_archivo: List[str],
        prompt_video: str,
        carpeta: str = "wordpress",
        duracion_segundos: int = 8,
        overwrite: bool = False
) -> Dict[str, object]:
    """Generador de videos desde archivos

    Args:
        nombre_archivo (List[str]): Lista de nombres de archivos de imagen.
        prompt_video (str): El prompt descriptivo del video.
        carpeta (str, optional): La carpeta donde se encuentran las imágenes. Defaults to "wordpress".
        duracion_segundos (int, optional): La duración deseada del video en segundos. Defaults to 8.
        overwrite (bool, optional): Si se debe sobrescribir un video existente. Defaults to False.

    Returns:
        Dict[str, object]: Un diccionario con el estado y la ruta del video generado o un mensaje de error.
    """
    base_dir=os.path.dirname(os.path.abspath(__file__))
    images_dir=os.path.join(os.path.dirname(base_dir), "images", carpeta)
    image_paths = [os.path.join(images_dir, n) for n in nombre_archivo]
    prompt = f"{prompt_video}. Short {duracion_segundos} seconds.  cinematic shot, smooth camera, natural motion."
    return generate_videos_for_list(
        image_paths=image_paths,
        prompt=prompt,
        overwrite=overwrite
    )

def generar_videos_en_carpeta(
        plataforma: str = "wordpress",
        prompt_video: str = "Bride walking gracefully in different locations, elegant, cinematic lighting",
        max_videos: int = 0,
        overwrite: bool = False
) -> Dict[str, object]:
    base_dir=os.path.dirname(os.path.abspath(__file__))
    image_dir=os.path.join(os.path.dirname(base_dir), "images", plataforma)
    prompt = f"{prompt_video}. Short 8 seconds.  cinematic shot, smooth camera, natural motion."
    return generate_videos_in_folder(
        images_dir=image_dir,
        prompt=prompt,
        max_videos=max_videos,
        overwrite=overwrite
    )


    """
# ----------------------------------------------------------------------
# 3. DEFINICIÓN DEL AGENTE RAÍZ (ADK)
# ----------------------------------------------------------------------
"""

e_commerce_agent = Agent(
    name="ecommerce_media_generator",
    model="gemini-2.5-flash",
    description=(
        "Agente experto en generación de contenido multimedia para plataformas de e-commerce."
    ),
    instruction=(
        "Tu objetivo es asistir al usuario en la creación de materiales de marketing (imágenes y videos). "
        "Usa 'extraer_imagenes_de_cms' para obtener imágenes de productos de cualquier CMS soportado. "
        "Luego, usa 'generar_video_veo' para convertir esas imágenes en videos promocionales. "
        "Sé flexible y creativo. Si el usuario pide un video, primero intenta obtener la imagen si es necesario, y luego genera el video."
    ),
    tools=[
        extraer_imagenes_de_cms, 
        generar_video_veo,
        generar_videos_desde_archivos,
        generar_videos_en_carpeta,], 
)

# ADK busca una variable llamada 'root_agent'
root_agent = e_commerce_agent