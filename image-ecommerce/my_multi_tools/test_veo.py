import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

# Forzar GOOGLE_APPLICATION_CREDENTIALS por si .env no se carga
cred = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cred = os.path.join(base_dir, os.getenv("GCP_SERVICE_ACCOUNT_KEY", "gcp-credentials.json"))
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred

if not os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]):
    raise FileNotFoundError(f"Credencial no encontrada: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")

project = os.getenv("GCP_PROJECT_ID")
location = os.getenv("GCP_LOCATION", "us-central1")

client = genai.Client(vertexai=True, project=project, location=location)
print(f"[X] Cliente Vertex listo ({project}/{location})")
print(f"[X] Credenciales: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")

prompt = "Cinematic slow-motion close-up of a wedding dress flowing gracefully, soft natural light, 4k, shallow depth of field"

# Generar video con Veo 2.0 (modelo disponible)
operation = client.models.generate_videos(
    model="veo-2.0-generate-001",
    prompt=prompt,
    config=types.GenerateVideosConfig(enhance_prompt=True),
)
print(f"[X] Operación iniciada: {operation.name}")
print("[X] Generando (5–10 min)...")

# Polling (refrescando el estado con el objeto Operation)
start = time.time()
timeout_sec = 780  # ~13 minutos
while not operation.done:
    elapsed = int(time.time() - start)
    if elapsed % 60 == 0:
        print(f"[!] Esperando... {elapsed//60}m")
    if elapsed >= timeout_sec:
        print("[!] Timeout. Verifica en consola Vertex AI:")
        print(f"    https://console.cloud.google.com/vertex-ai/generative/video?project={project}")
        print(f"    Operation: {operation.name}")
        raise SystemExit(0)
    time.sleep(20)
    # Refresca usando el objeto Operation (no pases strings)
    operation = client.operations.get(operation)

if not operation.response or not operation.response.generated_videos:
    raise RuntimeError("Operación completó pero no devolvió videos")

video = operation.response.generated_videos[0].video

# Extraer bytes de forma robusta
video_bytes = None
for attr in ("video_bytes", "bytes", "data"):
    val = getattr(video, attr, None)
    if val:
        video_bytes = val
        break

if not video_bytes and getattr(video, "uri", None):
    # Descargar vía Files API si viene como URI
    downloaded = client.files.download(name=video.uri)
    # algunos SDKs exponen .data, otros .bytes
    video_bytes = getattr(downloaded, "data", None) or getattr(downloaded, "bytes", None)

if not video_bytes:
    # Último recurso: mostrar atributos disponibles para depurar
    print(f"[!] Atributos de Video: {list(video.__dict__.keys()) if hasattr(video, '__dict__') else dir(video)}")
    raise AttributeError("No se encontraron bytes del video (video_bytes/bytes/data) ni uri descargable")

out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "veo_output.mp4")
with open(out_path, "wb") as f:
    f.write(video_bytes)

print(f"[X] Video guardado: {out_path}")
print(f"[X] Tamaño: {len(video_bytes)/(1024*1024):.2f} MB")