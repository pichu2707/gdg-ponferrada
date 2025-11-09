![Logo Javi Lazaro](https://github.com/pichu2707/gdg-ponferrada/blob/master/images/logos/V1__logo.png)
# Creación de Agentes IA con ADK y Gemini
Vamos a explicar como utilizar [ADK](https://google.github.io/adk-docs/) (Agent Developmen Kit) el **Framework de Google** para desarrolla y gestionar agentes IA.
ADK según nos dice Google **está optimizada para Gemini** pero esto no significa que no podamos utilizar otros Agentes IA como OpenAI, Anthropic o Ollama.

## Conceptos más importantes
ADK se basa en conceptos clave y primitaivas que lo hacen potente y flexible.

**Agente**: unidad de trabajo fundamental que está diseñado para realizar las tareas.
**Herramientas**: capacidades que ayudan a interactuar con API externas, buscar información, ejecutar código o llamar a otros servicios.
**Devoluciones de llamdas**: Código personalizado que tenemos que hacer nosotros mismos para ejecutrase en momentos esecídgicos del proceso del agente, que ayudará a este a realizar verificaciones, registros o modificaciones en los comportamientos.
**Gestión de sesiones** *(Session & State)*:Manejja el contexto de una sola conversación *(Session)*, incluido su historial *(Event)* y la memotría del trabajo del agente para esa conversación *(State)*.
**Memoria**: permite a los agentees recordar información sobre un usuario en múltiples sesiones, proporcionando un contexto a largo plazo *(distinto de una a corto plazo como State)*.
**Gestión de artefactos** *(Artifact)*: permite a los agentes guardar, cargar y administrar archivos o datos binarios como PDFs asociados a una sesión.
**Ejecución de código**: capacidade de los agentes, normalmente a través de herramientas de generar código y ejecutar código para realizar cálculos o acciones complejas.
**Planificación**: capacidad avanzada donde los agentes pueden dividir objetos complejos ne pasos más pequeños y planificar como alcanzarlos como un planificador ReAct.
**Modelos**: El LLM subyacente que potenicia *LlmAgent* a los estudiantes, posibilitando sus capacidades de razoniamiento y compresión de lenguaje.
**Evento**: unidad básica de comunicación que representa las cosas que suceden durante una sesión (mensaje del usuario, respuesta del agente, uso de la herramienta) y que forma el historial de conversación.
**Ejecutor**: motor que administra el flujo de ejecución, orquesta interecciones de los agentes en función de los eventos y se coordina con los servición de backend.

## Categorización de los agentes:
ADK nos da diferentes categorías de los agentes para poder crear estas aplicaciones.

1. **Agentes LLM (*LlmAgent*, *Agent*)**: Esos son los que como su nombre indican usan los LLM como motor principal para comprender el lenguaje natural, razonar, planificar, generar una respuesta y decidir dinámicamente como proceder o que herramientas puede utilizar.
2. **Agentes de flujo de trabajo (*SequentialAgent*, *ParalleAgent*, *LoopAgent*)**: Estos agentes estáan especializados en controlar el flujo de ejecución de otros agentes mediantes patrones predefinidos y determinista. Estos son ideales para procesos de estructurados que requiren una ejecución más predecible.
3. **Agentes personalizados**: Si como lees podemos crear agentes mediante la extensión **BaseAgent** directam estos agentes permiten ingtegrar una lógica operativa única, flujos de control específicos o integraciones especializadas no contempladas por tipos estandarizando.

## Herramientas:

ADK nois ofrece la forma de poder hacer que nuestros agentes puedan utilizar herramientas *tools*. Podemos crear las herramientas nosotros mismos o también nos ofrecen herramientas ya creadas por el equipo de Google a nuestra disposición.
ADK nos ofrece varias formas de crear herarmientas, cada uan con diferentes niveles de complejidad y control:

### **[Herramientas de función]('/README.md/#functions-tools')**: 
Transformacions una función de Python en una herramienta de forma sencilla de integrar lódiga personalizada a los agentes que montamos.

#### Cómo funciona
Un parámetro se considera **obligatorio** si tiene una indicación de tipo pero no un valor predeterminado . El LLM debe proporcionar un valor para este argumento al llamar a la herramienta. La descripción del parámetro se toma de la documentación de la función.

```python
def get_weather(city: str, unit: str):
    """
    Recupera el clima de una ciudad en la unidad especificada.

    Args:
        city (str): El nombre de la ciudad.
        unit (str): La unidad de medición de la temperatura, 'Celsius' o 'Fahrenheit'.
    """
    # ... función lógica ...
    return {"status": "success", "report": f"Weather for {city} is sunny."}
```

Por el caso contrario si le ponemos un valor predeterminado, este ya pasa a ser **opcional**

### **[Herramientas de función de larga duración]('/README.md/#functions-long-run-tools')**:
Estas funciones de larga duración están diseñadas para ayudar a iniciar y gestionar tareas que tengan unaduración larga como parte del flujo de trabajo para le agente, pero **no para ejecutar la tarea en si**. Si estas tareas llevan más tiempo de lo normal debería montarse en un servidor independiente.

#### Cómo funciona:
Vamos a crear python una función envuelta en `LongRunningFunctionTool`.
1. **Iniciación**: Cuando el LLM llama a la herramienta, su función inicia la operación de largaduración.
2. **Actualizaciones iniciales**: Su funión debería devolver opcionalmente un resultado inicial. El marco de trabajo del ADK toma el resultado y lo envía de vuelta al LLM empaaquetado en un bojeto `FunctionResponse`. Esto permite que el LLM informe al usuario por ejemplo estado de completado, mensajes...pasando a finalizar o pausar la acción.
3. **Continuar o esperar**: Tras finalizar cada ejecución del agente, el cliente puede consultar el progreso de la operación y decidir si continúa con una respuesta intermedia o esperar la respuesta final. El cliente debe enviar la respuesta intermedia o final agente para la siguiente ejecución.
4. **Gestión del framework**: El frame ADK en este caso gestiona la ejecución. Envía ael paquete intermedio o final `FinctionResponse`enviado por el cliente agente al LLM para generar un mensaje en lenguaje natural para el usuario.

```python
# 1. Define la función de tiempo largo
def ask_for_approval(
    purpose: str, amount: float
) -> dict[str, Any]:
    """Solicite aprobación para el reembolso."""
    # Crear un ticket para la aprobación
    # Enviar una notificación al aprobador con el enlace del ticket
    return {'status': 'pending', 'approver': 'Sean Zhou', 'purpose' : purpose, 'amount': amount, 'ticket-id': 'approval-ticket-1'}

def reimburse(purpose: str, amount: float) -> str:
    """Reembolsar la cantidad de dinero al empleado."""
    # enviar la solicitud de reembolso al proveedor de pagos
    return {'status': 'ok'}

# 2. Envuelva la función con LongRunningFunctionTool
long_running_tool = LongRunningFunctionTool(func=ask_for_approval)
```

### **[Agentes como herramientas]('/README.md/#agents-tools')**:
Esta función permite aprovechar las capacidades de otros agentes del sistema, invocándolos como herramientas. La  función de Agente como herramienta permie que otro agente realice una tarea específica, **delegando así la responsabilidad**.

#### Cómo funciona:

```python

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

APP_NAME="summary_agent"
USER_ID="user1234"
SESSION_ID="1234"

summary_agent = Agent(
    model="gemini-2.0-flash",
    name="summary_agent",
    instruction="""Eres un experto resumidor. Lea el siguiente texto y proporcione un resumen conciso.""",
    description="Agente para resumir texto",
)

root_agent = Agent(
    model='gemini-2.0-flash',
    name='root_agent',
    instruction="""Eres un asistente útil. Cuando el usuario proporcione un texto, utilice la herramienta 'resumir' para generar un resumen. Reenvíe siempre el mensaje del usuario exactamente como lo recibió a la herramienta 'resumir', sin modificarlo ni resumirlo usted mismo. Presentar la respuesta de la herramienta al usuario.""",
    tools=[AgentTool(agent=summary_agent, skip_summarization=True)]
)

# Sesión y Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner


# Interacción del agente
async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)


long_text = """La computación cuántica representa un enfoque fundamentalmente diferente de la computación, Aprovechar los extraños principios de la mecánica cuántica para procesar información. A diferencia de las computadoras clásicas que dependen de bits que representan 0 o 1, las computadoras cuánticas utilizan qubits que pueden existir en un estado de superposición, de manera efectiva siendo 0, 1 o una combinación de ambos simultáneamente. Además, los qubits pueden enredarse, lo que significa que sus destinos están entrelazados independientemente de la distancia, lo que permite correlaciones complejas. Este paralelismo y La interconexión otorga a las computadoras cuánticas el potencial de resolver tipos específicos de problemas increíblemente complejos, como como el descubrimiento de fármacos, la ciencia de los materiales, la optimización de sistemas complejos y la ruptura de ciertos tipos de criptografía más rápido de lo que incluso las supercomputadoras clásicas más potentes podrían lograr, aunque la tecnología aún se encuentra en gran medida en sus etapas de desarrollo."""


# Nota: En Colab, puedes usar directamente 'await' en el nivel superior. # Si ejecuta este código como un script Python independiente, deberá usar asyncio.run() o administrar el bucle de eventos.
await call_agent_async(long_text)
```

1. Cuando `main_agent`recibe el texto, sus instrucciones indican que utilice la herramienta 'resumir' para textos largos.
2. El marco reconoce 'summarice' como elementor `AgentTool` que envuelve el elementor `summary_agent`.
3. En un segundo plano, `main_agent`se llamará al programa `summary_agent`con el texto largo como entrada.
4. El `summary_agent`programa procesará el texto según sus instrucciones y generará un resumen.
5. La respuesta del `summary_agent`se devuelve entonces al `main_agent`.
6. Luego puede `main_agent`tomar el resuemn y formular su respuesta final al usuario


El colaboración con ![LIN3S](https://github.com/pichu2707/gdg-ponferrada/blob/master/images/logos/LIN3S-white.png)

✉️ Para cualquier consulta o mejora no dudes en escribirme a mi correo [hola@javilazaro.es](mailto:hola@javilazaro.es)ailto:hola@javilazaro.es)