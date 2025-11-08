"""
Genera un video por cada imagen encontrada en la carpeta `images/`.

Basado en: https://googleapis.github.io/python-genai/#generate-videos-image-to-video
Costo aproximado: $0.10–0.50 por video en GCP (usa con cuidado).
"""
import os
import mimetypes
import time
from typing import Optional, Tuple, List, Dict
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

# Credenciales
credentials_filename = os.getenv('GCP_SERVICE_ACCOUNT_KEY', 'gcp-credentials.json')
credentials_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    credentials_filename
)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
print(f"[X] Usando credenciales: {os.path.abspath(credentials_path)}")
if not os.path.exists(credentials_path):
    print(f"[!] ERROR: Archivo de credenciales no encontrado en {credentials_path}")
    exit(1)

# Cliente Vertex AI
try:
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GCP_PROJECT_ID"),
        location=os.getenv("GCP_LOCATION", "us-central1"),
    )
    print(f"[X] Cliente GCP inicializado correctamente")
    print(f"[X] Proyecto: {os.getenv('GCP_PROJECT_ID')}")
    print(f"[X] Región: {os.getenv('GCP_LOCATION')}")
except Exception as e:
    print(f"[!] Error al inicializar cliente GCP: {e}")
    exit(1)

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

def videos_output_dir() -> str:
    """Devuelve la carpeta 'videos' junto a 'images' en image-ecommerce/."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    videos_dir = os.path.join(root_dir, 'videos')
    os.makedirs(videos_dir, exist_ok=True)
    return videos_dir

def generate_videos_for_list(
        image_paths: List[str],
        *,
        prompt: str,
        overwrite: bool = False,
        timeout_sec: int = 1200,
    ) -> Dict[str, object]:
    """Genera videos para una lista de rutas de imagen."""
    print(f"[VEO] Procesando {len(image_paths)} imágenes")
    for img_path in image_paths:
        print(f"[VEO] Imagen: {img_path}, existe={os.path.isfile(img_path)}")
    
    out_dir = videos_output_dir()
    processed = 0
    skipped = 0
    failed = 0
    results: List[Dict[str, str]] = []

    for idx, src_path in enumerate(image_paths, start=1):
        if not os.path.isfile(src_path):
            print(f"[x] La imagen fuente no existe: {src_path}")
            failed += 1
            results.append({
                'image': src_path, 
                'status': 'failed', 
                'message': 'Imagen fuente no existe'
            })
            continue

        base = os.path.splitext(os.path.basename(src_path))[0]
        out_path = os.path.join(out_dir, f"{base}.mp4")
        print(f"[VEO] Guardando en: {out_path}")
        
        if os.path.exists(out_path) and not overwrite:
            print(f"[-] Ya existe, salto: {out_path}")
            skipped += 1
            results.append({
                'image': src_path, 
                'status': 'skipped', 
                'message': 'Ya existe'
            })
            continue

        video_bytes, err = generate_video_from_image(
            src_path, 
            prompt=prompt, 
            timeout_sec=timeout_sec
        )

        if err:
            print(f"[x] Error generando video: {err}")
            failed += 1
            results.append({
                'image': src_path, 
                'status': 'failed', 
                'message': err
            })
            continue

        try:
            with open(out_path, 'wb') as f:
                f.write(video_bytes)  # type: ignore[arg-type]
            size_mb = (len(video_bytes) if video_bytes else 0) / (1024 * 1024)
            print(f"[✔] Video guardado: {out_path} ({size_mb:.2f} MB)")
            processed += 1
            results.append({
                'image': src_path,
                'video_path': out_path,
                'status': 'processed',
            })
        except Exception as e:
            print(f"[x] Error guardando archivo: {e}")
            failed += 1
            results.append({
                'image': src_path, 
                'status': 'failed', 
                'message': str(e)
            })

    return {
        'status': 'success',
        'processed': processed,
        'skipped': skipped,
        'failed': failed,
        'videos_dir': out_dir,
        'results': results,
    }
    
def generate_videos_in_folder(
        images_dir: str,
        *,
        prompt: str,
        max_videos: int = 0,
        overwrite: bool = False,
        timeout_sec: int = 1200,
) -> Dict[str, object]:
    """Genera videos para todas las imágenes soportadas en una carpeta."""
    if not os.path.isdir(images_dir):
        return {
            'status': 'error',
            'message': f"La carpeta de imágenes no existe: {images_dir}"
        }
    
    all_files = sorted(os.listdir(images_dir))
    paths = [
        os.path.join(images_dir, f)
        for f in all_files
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS
    ]
    
    if max_videos and len(paths) > max_videos:
        paths = paths[:max_videos]
    
    return generate_videos_for_list(
        paths,
        prompt=prompt,
        overwrite=overwrite,
        timeout_sec=timeout_sec,
    )

def ensure_webp_mimetype() -> None:
    """Asegura que el mimetype de .webp esté registrado."""
    if not mimetypes.guess_type('dummy.webp')[0]:
        mimetypes.add_type('image/webp', '.webp')

def guess_mime_type(path: str) -> str:
    """Obtiene un MIME type robusto basado en mimetypes/extensión."""
    mime, _ = mimetypes.guess_type(path)
    if mime:
        return mime
    ext = os.path.splitext(path)[1].lower()
    return {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.gif': 'image/gif', '.webp': 'image/webp',
    }.get(ext, 'image/jpeg')

def generate_video_from_image(
    image_path: str, 
    *, 
    prompt: str, 
    timeout_sec: int = 1200,
    model: str = 'veo-2.0-generate-001',
) -> Tuple[Optional[bytes], Optional[str]]:
    """Genera un video desde una imagen usando Veo 2."""
    print(f"[VEO] Generando video desde: {image_path}")
    print(f"[VEO] Prompt: {prompt[:100]}...")
    
    try:
        ensure_webp_mimetype()
        mime_type = guess_mime_type(image_path)
        print(f"[VEO] MIME type: {mime_type}")

        with open(image_path, "rb") as f:
            image_bytes_data = f.read()
        image = types.Image(image_bytes=image_bytes_data, mime_type=mime_type)

        print(f"[VEO] Iniciando generación de video para '{os.path.basename(image_path)}'…")

        operation = client.models.generate_videos(
            model=model,
            prompt=prompt,
            image=image,
            config=types.GenerateVideosConfig(
                enhance_prompt=True,
            ),
        )

        op_name = operation.name if hasattr(operation, 'name') else str(operation)
        print(f"[VEO] Operación lanzada: {op_name}")

        # Sondeo hasta completar
        start_time = time.time()
        last_min_logged = -1
        
        while not getattr(operation, "done", False):
            elapsed = time.time() - start_time
            elapsed_min = int(elapsed // 60)
            if elapsed_min != last_min_logged:
                print(f"[!] Esperando… {elapsed_min}m")
                last_min_logged = elapsed_min
            if elapsed >= timeout_sec:
                return None, f"Timeout tras {timeout_sec // 60} minutos"
            time.sleep(15)
            try:
                # CORRECCIÓN: pasar el objeto operation
                operation = client.operations.get(operation)
            except Exception as refresh_err:
                print(f"[!] Error refrescando operación: {refresh_err}")
            
        print(f"[VEO] Operación completada")

        response = getattr(operation, "response", None)
        if not response:
            return None, "Operación sin respuesta"
        
        generated = getattr(response, "generated_videos", None)
        if not generated:
            return None, "Operación sin videos generados"

        first = generated[0]
        video = getattr(first, "video", None)
        if not video:
            return None, "Respuesta sin objeto video"

        video_bytes = (
            getattr(video, "video_bytes", None) or
            getattr(video, "bytes", None) or
            getattr(video, "data", None)
        )
        
        if not video_bytes and getattr(video, "uri", None):
            uri = video.uri
            print(f"[VEO] Descargando video desde URI: {uri}")
            try:
                downloaded = client.files.download(name=uri)
                video_bytes = (
                    getattr(downloaded, "video_bytes", None) or
                    getattr(downloaded, "bytes", None) or
                    getattr(downloaded, "data", None)
                )
            except Exception as download_err:
                print(f"[!] Error descargando video desde URI: {download_err}")

        if not video_bytes:
            return None, "Video sin bytes/uri"

        size_mb = len(video_bytes) / (1024 * 1024)
        print(f"[VEO] Video generado exitosamente ({size_mb:.2f} MB)")
        return video_bytes, None
    
    except Exception as e:
        print(f"[VEO ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        msg = str(e)
        if "PERMISSION_DENIED" in msg or "403" in msg:
            msg += " | Tip: rol Vertex AI User"
        elif "FAILED_PRECONDITION" in msg or "billing" in msg.lower():
            msg += " | Tip: activar facturación"
        elif "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
            msg += " | Tip: revisar cuotas"
        elif "NOT_FOUND" in msg or "404" in msg:
            msg += " | Tip: región us-central1 y modelo correcto"
        return None, msg

def main() -> None:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    images_dir = os.path.join(root_dir, 'images')
    videos_dir = os.path.join(root_dir, 'videos')
    os.makedirs(videos_dir, exist_ok=True)

    if not os.path.isdir(images_dir):
        print(f"[!] Carpeta de imágenes no encontrada: {images_dir}")
        exit(1)

    prompt_default = os.getenv(
        "VIDEO_PROMPT",
        "A short elegant video of a wedding dress flowing gracefully in the wind, cinematic lighting",
    )

    try:
        max_videos = int(os.getenv("MAX_VIDEOS", "0"))
    except ValueError:
        max_videos = 0

    all_files = sorted(os.listdir(images_dir))
    image_files = [f for f in all_files if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS]
    
    if not image_files:
        print(f"[!] No se encontraron imágenes en {images_dir}")
        exit(0)

    print(f"[X] Encontradas {len(image_files)} imágenes. Generando videos en: {videos_dir}")
    print(f"[!] Nota de costos: esto puede generar cargos en GCP.")

    processed = 0
    skipped = 0
    failed = 0

    for idx, filename in enumerate(image_files, start=1):
        src_path = os.path.join(images_dir, filename)
        base, _ = os.path.splitext(filename)
        out_path = os.path.join(videos_dir, f"{base}.mp4")

        if os.path.exists(out_path):
            print(f"[-] Ya existe, salto: {out_path}")
            skipped += 1
            continue

        if max_videos and processed >= max_videos:
            print(f"[i] Alcanzado MAX_VIDEOS={max_videos}, deteniendo.")
            break

        print(f"\n[{idx}/{len(image_files)}] Procesando: {filename}")
        video_bytes, err = generate_video_from_image(src_path, prompt=prompt_default)
        
        if err:
            print(f"[x] Falló '{filename}': {err}")
            failed += 1
            continue

        try:
            with open(out_path, 'wb') as f:
                f.write(video_bytes)  # type: ignore[arg-type]
            size_mb = (len(video_bytes) if video_bytes else 0) / (1024 * 1024)
            print(f"[✔] Guardado: {out_path} ({size_mb:.2f} MB)")
            processed += 1
        except Exception as e:
            print(f"[x] Error guardando '{out_path}': {e}")
            failed += 1

    print("\n===== Resumen =====")
    print(f"Procesados: {processed}")
    print(f"Saltados:   {skipped}")
    print(f"Fallidos:   {failed}")
    print("===================\n")

if __name__ == "__main__":
    main()