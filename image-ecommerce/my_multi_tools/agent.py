import os
from dotenv import load_dotenv
load_dotenv(override=True)

def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _resolve_image_path(name_or_path: str, carpeta: str = "wordpress") -> str:
    p = (name_or_path or "").strip().strip("'").strip('"')
    if not p:
        return p
    if os.path.isabs(p):
        return os.path.normpath(p)
    p = p.replace("\\", "/")
    root = _project_root()
    if p.lower().startswith("image-ecommerce/images/"):
        rel = p.split("image-ecommerce/", 1)[-1]
        return os.path.normpath(os.path.join(root, rel))
    if p.lower().startswith("images/"):
        return os.path.normpath(os.path.join(root, p))
    base = os.path.basename(p)
    return os.path.normpath(os.path.join(root, "images", carpeta, base))

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

def generar_video_veo(
        nombre_archivo: str,
        ruta_imagen_origen: str, 
        prompt_video: str, 
        carpeta: str = "wordpress",
        duracion_segundos: int = 8,
        overwrite: bool = False
        ) -> Dict[str, str]:
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
    
    from .veo_images_videos import generate_videos_for_list
    image_path = _resolve_image_path(nombre_archivo, carpeta)
    print(f"[PATH] {image_path} existe={os.path.isfile(image_path)}")
    prompt = f"{prompt_video}. Short {duracion_segundos} seconds. cinematic shot, smooth camera, natural motion."
    return generate_videos_for_list(
        image_paths=[image_path],
        prompt=prompt,
        overwrite=overwrite
    )

def listar_imagenes_en_carpeta(plataforma: str = "wordpress") -> Dict[str, object]:
    images_dir = os.path.join(_project_root(), "images", plataforma)
    if not os.path.isdir(images_dir):
        return {"status": "error", "message": f"No existe: {images_dir}"}
    soportadas = {".jpg",".jpeg",".png",".gif",".webp"}
    files = [f for f in os.listdir(images_dir) if os.path.splitext(f)[1].lower() in soportadas]
    return {"status": "success", "dir": images_dir, "count": len(files), "files": files[:500]}

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
    from .veo_images_videos import generate_videos_for_list
    image_paths = [_resolve_image_path(n, carpeta) for n in nombre_archivo]
    for p in image_paths:
        print(f"[PATH] {p} existe={os.path.isfile(p)}")
    prompt = f"{prompt_video}. Short {duracion_segundos} seconds. cinematic shot, smooth camera, natural motion."
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
        generar_videos_en_carpeta,
        listar_imagenes_en_carpeta], 
)

# ADK busca una variable llamada 'root_agent'
root_agent = e_commerce_agent