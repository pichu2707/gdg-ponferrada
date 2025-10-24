# Creación de Agentes IA con ADK y Gemini
Vamos a explicar como utilizar [ADK](https://google.github.io/adk-docs/) (Agent Developmen Kit) el **Framework de Google** para desarrolla y gestionar agentes IA.
ADK según nos dice Google **está optimizada para Gemini** pero esto no significa que no podamos utilizar otros Agentes IA como OpenAI, Anthropic o Ollama.

## Categorización de los agentes:
ADK nos da diferentes categorías de los agentes para poder crear estas aplicaciones.

1. **Agentes LLM (*LlmAgent*, *Agent*)**: Esos son los que como su nombre indican usan los LLM como motor principal para comprender el lenguaje natural, razonar, planificar, generar una respuesta y decidir dinámicamente como proceder o que herramientas puede utilizar.
2. **Agentes de flujo de trabajo (*SequentialAgent*, *ParalleAgent*, *LoopAgent*)**: Estos agentes estáan especializados en controlar el flujo de ejecución de otros agentes mediantes patrones predefinidos y determinista. Estos son ideales para procesos de estructurados que requiren una ejecución más predecible.
3. **Agentes personalizados**: Si como lees podemos crear agentes mediante la extensión **BaseAgent** directam estos agentes permiten ingtegrar una lógica operativa única, flujos de control específicos o integraciones especializadas no contempladas por tipos estandarizando.

✉️ Para cualquier consulta o mejora no dudes en escribirme a mi correo [hola@javilazaro.es](mailto:hola@javilazaro.es)