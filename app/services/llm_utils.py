import os
from dotenv import load_dotenv
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from app.schemas.hse_schemas import IncidentAnalysisResponse

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def get_hse_agent():
    """
    Crea un Agente HSE siguiendo las mejores prácticas de la documentación:
    1. Uso de 'create_agent' para producción.
    2. Salida estructurada nativa (Structured Output) vía 'response_format'.
    3. Caching de Prompt de Sistema (si el proveedor lo soporta nativamente).
    """
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL ERROR: ANTHROPIC_API_KEY no encontrada en variables de entorno.")

    # Instrucciones sistemáticas
    # Nota: El formato y caché se manejan mejor via SystemMessage estructurado
    system_content_text = """
    Eres un Investigador Senior de Incidentes y Accidentes HSE.
    
    Tu tarea es analizar incidentes usando la metodología de los "5 Porqués".
    
    METODOLOGÍA:
    - Comienza por el problema directo descrito.
    - Pregunta "¿Por qué?" iterativamente (5 niveles).
    - Encuentra la fallas en el proceso o sistema, no solo errores humanos.
    
    Analiza la información proporcionada y genera SIEMPRE una salida estructurada.
    """

    # Definimos el mensaje de sistema. 
    # Intentamos usar la estructura de caché mencionada en la doc si es compatible con el driver actual.
    system_message = SystemMessage(
        content=[
            {
                "type": "text",
                "text": system_content_text,
                # "cache_control": {"type": "ephemeral"} # Descomentar si la versión de API soporta beta headers explícitos
            }
        ]
    )

    model = ChatAnthropic(
        api_key=api_key,
        model="claude-3-5-sonnet-20241022",
        temperature=0.1
    )

    # Creamos el agente usando la implementación oficial de producción
    # Pasamos IncidentAnalysisResponse a response_format para obtener JSON garantizado sin parsing manual
    agent = create_agent(
        model=model,
        tools=[], 
        system_prompt=system_message,
        response_format=IncidentAnalysisResponse, 
        checkpointer=MemorySaver()
    )
    
    return agent




