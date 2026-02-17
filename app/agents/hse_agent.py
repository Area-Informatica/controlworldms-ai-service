
from langchain.agents import create_agent
from app.schemas.hse_schemas import IncidentAnalysisResponse
from app.prompts.hse_prompts import HSE_5PORQUE_SYSTEM_PROMPT

def get_hse_agent():
    """
    Crea un Agente HSE siguiendo las mejores prácticas de la documentación:
    1. Uso de 'create_agent' para producción.
    2. Salida estructurada nativa (Structured Output) vía 'response_format'.
    3. Uso de modelo Claude estándar.
    """

    # Creamos el agente
    agent = create_agent(
        model="claude-3-haiku-20240307", #"claude-sonnet-4-5-20250929",
        tools=[], 
        system_prompt=HSE_5PORQUE_SYSTEM_PROMPT,
        response_format=IncidentAnalysisResponse
    )
    
    return agent
