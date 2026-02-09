import os
from dotenv import load_dotenv
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from app.schemas.hse_schemas import IncidentAnalysisResponse

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def get_hse_agent():
    """
    Crea un Agente HSE siguiendo las mejores prácticas de la documentación:
    1. Uso de 'create_agent' para producción.
    2. Salida estructurada nativa (Structured Output) vía 'response_format'.
    3. Uso de modelo Claude estándar sin caché (dado el bajo volumen de peticiones).
    """
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL ERROR: ANTHROPIC_API_KEY no encontrada en variables de entorno.")

    # Instrucciones sistemáticas
    system_content_text = """
    Eres un Investigador Senior de Incidentes y Accidentes HSE (Salud, Seguridad y Medio Ambiente).
    
    Tu tarea es analizar incidentes usando la metodología de los "5 Porqués".
    
    METODOLOGÍA:
    - Comienza por el problema directo descrito.
    - Pregunta "¿Por qué?" iterativamente (5 niveles).
    - Encuentra la fallas en el proceso o sistema, no solo errores humanos.
    
    Analiza la información proporcionada y genera SIEMPRE una salida estructurada.
    """

    # Mensaje de sistema limpio, sin configuración de caché
    system_message = SystemMessage(content=system_content_text)

    model = ChatAnthropic(
        api_key=api_key,
        model="claude-3-5-sonnet-20241022",
        temperature=0.1
    )

    # Creamos el agente
    # Nota: Eliminamos MemorySaver (checkpointer) si no necesitamos persistencia de sesión a largo plazo,
    # ya que para una simple petición y respuesta (REST API) no es estrictamente necesario y simplifica el grafo.
    agent = create_agent(
        model=model,
        tools=[], 
        system_prompt=system_message,
        response_format=IncidentAnalysisResponse
    )
    
    return agent




