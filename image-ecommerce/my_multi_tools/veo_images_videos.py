"""
Genera un video por cada imagen encontrada en la carpeta `images/`.

Basado en: https://googleapis.github.io/python-genai/#generate-videos-image-to-video
Costo aproximado: $0.10–0.50 por video en GCP (usa con cuidado).
"""
import os
import time
import mimetypes
from typing import Optional, Tuple
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

# Imagen de entrada
image_path = 'images/vestido-novia-riadra-atelierromance-encaje-escotev-espaldaabierta-atelierdebodas.webp'
if not mimetypes.guess_type('test.webp')[0]:
    mimetypes.add_type('image/webp', '.webp')
mime_type, _ = mimetypes.guess_type(image_path)
if mime_type is None:
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.gif': 'image/gif', '.webp': 'image/webp',
    }.get(ext, 'image/webp')

print(f"[X] Usando MIME type: {mime_type} para la imagen {image_path}")
with open(image_path, "rb") as f:
    image_bytes_data = f.read()
image = types.Image(image_bytes=image_bytes_data, mime_type=mime_type)

print(f"[!] NOTA: Esto tiene costo en GCP (~$0.10-0.50 por video)")

try:
    print(f"[X] Iniciando generación de video...")

    # Modelo estable (evita preview 3.1)
    operation = client.models.generate_videos(
        model='veo-2.0-generate-001',
        prompt='A short elegant video of a wedding dress flowing gracefully in the wind, cinematic lighting',
        image=image,
        config=types.GenerateVideosConfig(
            enhance_prompt=True,
            # duration_seconds y aspect_ratio pueden no estar soportados en 2.0
        ),
    )
    if operation is None:
        print(f"[!] ERROR: No se pudo iniciar la generación de video")
        exit(1)

    print(f"[X] Operación iniciada: {operation.name}")
    print(f"[X] Generando (5–10 min)...")

    # Polling con refresco de la operación
    start_time = time.time()
    timeout_sec = 780  # ~13 minutos
    while not operation.done:
        elapsed = int(time.time() - start_time)
        if elapsed % 60 == 0:
            except Exception as e:
        if elapsed >= timeout_sec:
            print(f"\n[!] Timeout alcanzado después de {timeout_sec // 60} minutos")
            print(f"[!] ID de operación: {operation.name}")
            SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


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
                }.get(ext, 'image/webp')


            def generate_video_from_image(image_path: str, *, prompt: str, timeout_sec: int = 780) -> Tuple[Optional[bytes], Optional[str]]:
                """
                Lanza la generación de video en Vertex AI para una imagen dada y devuelve (video_bytes, error_msg).
                No propaga excepciones: devuelve el error en el segundo valor para continuar el bucle.
                """
                try:
                    ensure_webp_mimetype()
                    mime_type = guess_mime_type(image_path)
                    print(f"[X] Usando MIME type: {mime_type} para la imagen {image_path}")

                    with open(image_path, "rb") as f:
                        image_bytes_data = f.read()
                    image = types.Image(image_bytes=image_bytes_data, mime_type=mime_type)

                    print(f"[X] Iniciando generación de video para '{os.path.basename(image_path)}'…")

                    operation = client.models.generate_videos(
                        model='veo-2.0-generate-001',
                        prompt=prompt,
                        image=image,
                        config=types.GenerateVideosConfig(
                            enhance_prompt=True,
                        ),
                    )
                    if operation is None:
                        return None, "No se pudo iniciar la operación"

                    print(f"[X] Operación iniciada: {getattr(operation, 'name', '(sin nombre)')}")
                    print(f"[X] Generando (5–10 min)…")

                    start_time = time.time()
                    while not operation.done:
                        elapsed = int(time.time() - start_time)
                        # Logea cada ~60s sin saturar la salida
                        if elapsed % 60 == 0:
                            print(f"[!] Esperando… {elapsed//60}m")
                        if elapsed >= timeout_sec:
                            return None, f"Timeout tras {timeout_sec // 60} minutos (op={getattr(operation, 'name', '?')})"
                        time.sleep(20)
                        # refrescar operación (algunas SDKs requieren el nombre; mantenemos compat)
                        try:
                            operation = client.operations.get(operation)
                        except Exception:
                            # Si falla el refresco, intentamos con el nombre (si existe)
                            op_name = getattr(operation, 'name', None)
                            if op_name:
                                operation = client.operations.get(op_name)

                    if not operation.response or not operation.response.generated_videos:
                        return None, f"Operación sin videos generados: {operation.response}"

                    video = operation.response.generated_videos[0].video
                    video_bytes = getattr(video, "video_bytes", None) or getattr(video, "bytes", None) or getattr(video, "data", None)
                    if not video_bytes and getattr(video, "uri", None):
                        downloaded = client.files.download(name=video.uri)
                        video_bytes = getattr(downloaded, "data", None) or getattr(downloaded, "bytes", None)

                    if not video_bytes:
                        return None, f"Video sin bytes/uri. Attrs: {dir(video)}"

                    return video_bytes, None

                except Exception as e:
                    msg = str(e)
                    if "PERMISSION_DENIED" in msg or "403" in msg:
                        msg += " | Tip: añade 'Vertex AI User' a la service account"
                    elif "FAILED_PRECONDITION" in msg or "billing" in msg.lower():
                        msg += " | Tip: activa la facturación"
                    elif "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                        msg += " | Tip: revisa cuotas"
                    elif "NOT_FOUND" in msg or "404" in msg:
                        msg += " | Tip: usa us-central1 y veo-2.0-generate-001"
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

                # Parámetro opcional: limitar cantidad (para evitar costos grandes)
                try:
                    max_videos = int(os.getenv("MAX_VIDEOS", "0"))
                except ValueError:
                    max_videos = 0

                # Recolectar imágenes soportadas
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

                    # Saltar si ya existe
                    if os.path.exists(out_path):
                        print(f"[-] Ya existe, salto: {out_path}")
                        skipped += 1
                        continue

                    # Límite opcional
                    if max_videos and processed >= max_videos:
                        print(f"[i] Alcanzado MAX_VIDEOS={max_videos}, deteniendo el bucle.")
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