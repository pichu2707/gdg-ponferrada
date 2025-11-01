'''
main.py: Ejemplo de un agente simple con ADK que usa una herramienta simulada.
'''
from agent_toolkit import Agent, tool

# --- Herramienta Simulada para VEO ---
# En un caso real, esta función usaría una librería como `requests`
# para hacer una llamada a la API de VEO con una clave de API.

@tool
def get_last_veo_video(query: str) -> str:
    '''
    Busca el último vídeo en la plataforma VEO.
    Simplemente devuelve un resultado de ejemplo.
    El parámetro "query" no se usa en este ejemplo, pero muestra cómo el agente puede pasar información.
    '''
    print(f"--- Herramienta: Buscando el último vídeo con la consulta: '{query}' ---")
    # Simulación de una respuesta de la API
    return "El último vídeo encontrado es 'Final GDG Ponferrada vs. León' (ID: video_12345)."

# --- Creación y ejecución del Agente ---
def main():
    '''Función principal para ejecutar el agente.'''
    # 1. Crear el agente
    agent = Agent()

    # 2. Añadir la herramienta al registro del agente
    agent.tool_registry.register(get_last_veo_video)

    # 3. Definir la pregunta (prompt) para el agente
    prompt = "¿Cuál fue el último partido que se grabó en VEO?"

    print(f"Usuario: {prompt}")

    # 4. Ejecutar el agente con el prompt
    result = agent.run(prompt)

    # 5. Imprimir el resultado final
    print(f"Agente: {result}")

if __name__ == "__main__":
    main()