
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from app.schemas.hse_schemas import IncidentAnalysisResponse
from app.services.llm_utils import get_llm_model
from app.prompts.hse_prompts import HSE_AGENT_SYSTEM_PROMPT

def get_hse_agent():
    """
    Crea un Agente HSE siguiendo las mejores prácticas de la documentación:
    1. Uso de 'create_agent' para producción.
    2. Salida estructurada nativa (Structured Output) vía 'response_format'.
    3. Uso de modelo Claude estándar sin caché (dado el bajo volumen de peticiones).
    """

    # Obtener el modelo base
    model = get_llm_model(model_name="claude-sonnet-4-5-20250929", temperature=0.1)

    # Mensaje de sistema limpio
    system_message = SystemMessage(content=HSE_AGENT_SYSTEM_PROMPT)

    # Creamos el agente
    agent = create_agent(
        model=model,
        tools=[], 
        system_prompt=system_message,
        response_format=IncidentAnalysisResponse
    )
    
    return agent
