from google.adk.agents.llm_agent import Agent 

def get_current_time(city: str) -> dict:
    """
    Obtiene la hora actual en una ciudad dada.
    Args:
        city (str): Nombre de la ciudad.
    Returns:
        dict: Un diccionario con la hora actual.
    """
    return {
        "status": "success",
         "city": city,
         "time": "10:30 AM"
        }

# Esto se puede montar con el comando `uv run adk create <nombre_del_agente>`

root_agent = Agent(
    model='gemini-2.5-flash', # Modelo de LLM
    name='Agente_Tiempo', # Nombre del agente
    description='Un agente que proporciona la hora actual en una ciudad dada.', # Descripción del agente
    instruction='Eres un asistente útil que indica la hora actual en las ciudades. Utiliza la herramienta «get_current_time» para este fin.', # Instrucciones para el agente
    tools=[get_current_time], # Herramientas disponibles para el agente
)