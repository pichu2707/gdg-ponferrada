from my_multi_tools.wordpress_downloader import WordPressMediaDownload

TARGET_URL = 'https://atelierdebodas.com/'  # Reemplaza con la URL de tu sitio WordPress
IMAGES_TO_DOWNLOAD = 5  # Número de imágenes a descargar
DESTINATION_FOLDER = 'images'  # Carpeta donde se guardarán las imágenes

def run_test():
    """
    Este es nuestro agente. Orquesta la herramienta para una prueba limitada
    """
    print("--- Iniciando la descarga de imágenes desde WordPress ---")
    # 1. Inicializar la herramienta de descarga
    downloader = WordPressMediaDownload(wordpress_url=TARGET_URL)

    # 2. Obtener las URLs de las imágenes
    all_urls = downloader.fetch_media_urls()

    if not all_urls:
        print("No se encontraron imágenes para descargar.")
        return
    
    # 3. Descargar un número limitado de imágenes
    test_urls = all_urls[:IMAGES_TO_DOWNLOAD]
    print(f"\\nSe usarán las primeras {len(test_urls)} imágenes para la prueba.")

    # 4. Ejecutar la descarga solo con la lista de prueba
    downloader.download_images(urls=test_urls, destination_folder=DESTINATION_FOLDER)
    print("\\--- Prueba de descarga completada ---")
    print(f"Las imágenes se han guardado en la carpeta: {DESTINATION_FOLDER}")

if __name__ == "__main__":
    run_test()