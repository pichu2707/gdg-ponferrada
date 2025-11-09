![Logo Javi Lazaro]('./images/logos/V1__logo.png')
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

El colaboración con ![LIN3S]('./images/logos/LIN3S-white.png')
✉️ Para cualquier consulta o mejora no dudes en escribirme a mi correo [hola@javilazaro.es](mailto:hola@javilazaro.es)ailto:hola@javilazaro.es)