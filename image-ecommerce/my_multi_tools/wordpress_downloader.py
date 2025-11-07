import requests
import os
import json
import time

class WordPressMediaDownload:
    """
    Una herramienta para descargar las imágenes a través de una API desde la carpeta de medias WordPress
    """
    def __init__(self, wordpress_url: str):
        """ 
        Inicializa el descargador con la URL del sitio WordPress

        Args:
            wordpress_url (str): La URL del sitio WordPress
        """
        if not wordpress_url.startswith(("http://", "https://")):
            raise ValueError("La URL de WordPress debe comenzar con http:// o https://")
        self.base_url = wordpress_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/wp-json/wp/v2/media"
        self.exclude_keywords = ['screenshot', 'elementor', 'logo', 'icon', 'banner', 'filtros', 'background']

    def _is_potential_image(self, media_item: dict) -> bool:
        """Aplica heurísticas para determinar si una imagen es probablemente una foto de producto

        Args:
            media_item (dict): El elemento de medios a evaluar

        Returns:
            bool: True si la imagen pasa los filtros, False en caso contrario
        """
        # 1º Filtro
        if media_item.get('media_type') != 'image':
            return False
        
        source_url = media_item.get('source_url', '').lower()
        if not source_url:
            return False
        
        # 2º Filtro: El nombre del archivo no debe contener palabras clave excluidas
        for keyword in self.exclude_keywords:
            if keyword in source_url:
                print(f"Filtrado por palabra clave {keyword}: {source_url}")
                return False
            
        # 3º Filtro: La imagen debe tener dimensiones mínimas (ejemplo: al menos 300x300)
        media_details = media_item.get('media_details', {})
        width = media_details.get('width', 0)
        height = media_details.get('height', 0)
        min_dimension = 300
        if width < min_dimension or height < min_dimension:
            print(f"Filtrado por dimensiones insuficientes ({width}x{height}): {source_url}")
            return False
        return True

    def fetch_media_urls(self) -> list[str]:
        """
        Recupera todas las URLs de imágenes de la API de medios, manejando la paginación

        Returns:
            list[str]: Una lista de URLs de imágenes
        """
        all_image_urls = []
        page = 1
        per_page = 10 # Este valor lo podemos ajusta a las páginas que queramos

        print(f"Inicializando la obtención de URLs desde {self.api_endpoint}")

        while True:
            params = {
                'per_page': per_page,
                'page': page
            }
            try:
                response = requests.get(
                    self.api_endpoint, 
                    params=params, 
                    timeout=30
                    )
                response.raise_for_status() # Lanza un error para códigos de estado 4xx/5xx
                media_items = response.json()

                if not media_items:
                    print("No se encontraron más elementos de medios.")
                    break

                for item in media_items:
                    # Nos asguramos de que el item es una imagen y tiene la URL
                    if self._is_potential_image(item):
                        all_image_urls.append(item['source_url'])
                    print(f"Página {page}: Obtenidas {len(media_items)} URLs de imágenes.")
                    page += 1

                    print("Esperando 1 segundo para evitar sobrecargar el servidor...")
                    time.sleep(1)  # Pausa para evitar sobrecargar el servidor

            except requests.exceptions.Timeout as e:
                print(f"Error: el servidor no respondió a tiempo en la página {page}. {e}")
                break
            except requests.exceptions.RequestException as e:
                print(f"Error al conectarse a la API de WordPress: {e}")
                break
            except json.JSONDecodeError:
                print(f"Error: la respuesta de la API en la página {page} no es JSON válido.")
                break

        print(f"Se encontraron un total de {len(all_image_urls)} URLs de imágenes.")
        return all_image_urls

    def download_images(self, urls: list[str], destination_folder: str = 'images'):
        """DEscarga imágenes desde una lista de URLs a una carpeta de destino

        Args:
            urls (list[str]): Lista de URLs de imágenes a descargar
            destination_folder (str, optional): Carpeta de destino para las imágenes descargadas. Defaults to 'images'.
        """
        if not urls:
            print("No hay URLs para descargar.")
            return
        
        print(f"Creando directorio de destino: {destination_folder}")
        os.makedirs(destination_folder, exist_ok=True)

        for url in urls:
            try:
                # Estraer el nombre del fichero de la URL
                filename = url.split('/')[-1]
                filepath = os.path.join(destination_folder, filename)

                if os.path.exists(filepath):
                    print(f"El archivo {filename} ya existe. Saltando descarga.")
                    continue

                print(f"Descargando {url} -> {filepath}")
                with requests.get(url, stream=True, timeout=15) as r:
                    r.raise_for_status()
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            except requests.exceptions.RequestException as e:
                print(f"Error al descargar {url}: {e}")
            except Exception as e:
                print(f"Error inesperado al descargar {url}: {e}")

    def run(self, destination_folder: str = 'images'):
        """Método principal para obtener las URLs de imágenes y descargarlas

        Args:
            destination_folder (str, optional): Carpeta de destino para las imágenes descargadas. Defaults to 'images'.
        """
        print("Iniciando el proceso de descarga de imágenes desde WordPress...")
        media_urls = self.fetch_media_urls()
        if media_urls:
            self.download_images(media_urls, destination_folder)
        print("Proceso de descarga completado.")

            