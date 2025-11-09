import datetime
from zoneinfo import ZoneInfo
from google.adk.agents.llm_agent import Agent


#Creamos una función para tomar el tiempo de una ciudad específica, en este caso de Ponferrada
def get_weather(city: str) -> dict:
    """Nos da el informe meterológico actual de una ciudad específica

    Args:
        city (str): Nombnre de la ciudad

    Returns:
        dict: Informe meteorológico de la ciudad o error
    """
    # Mock implementation
    if city.lower() == "ponferrada":
        return {
            "status": "success", 
            "report": (
                    "El tiempo en Ponferrada es soleado con 25°C."
                    "La temperatura máxima es de 28°C y la mínima de 15°C."
                    )
            }
    else:
        return {
            "status": "error", 
            "message": f"No se pudo obtener el informe meteorológico para {city}."
            }
    
# Creamos una función para obtener la hora actual de una ciudad específica
def get_current_time(city: str) -> dict:
    """Devuelve la hora de la ciudad especificada

    Args:
        city (str): El nombre de la ciudad

    Returns:
        dict: La hora actual de la ciudad o un error
    """

    if city.lower() == "ponferrada":
        tz_identifier = "Europe/Madrid"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Lo siento poero no tengo información sobre la hora en {city}."
            ),
        }
    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'La hora actual en {city} es {now.strftime("%H:%M")}'
    )
    return {
        "status": "success",
        "city": city,
        "time": report,
    }

# Definimos el agente raíz que utilizará las dos herramientas anteriores
root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.5-flash",
    description=(
        "Un agente que proporciona informes meteorológicos y la hora actual en ciudades específicas."
        ),
    instruction=(
        "Responde a las preguntas del usuario sobre el clima y la hora actual en diferentes ciudades."
    ),    
    tools=[get_weather, get_current_time],
    )

"""
Para la activación tenemos las dos maneras:
1. Usando la terminal:
    uv run adk run multi-tools/my_multi_tools/
2. Usando la web:
    uv run adk web --port 8000 ./multi-tools/
"""