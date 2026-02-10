"""
Agente de estandarización de artículos.
Arquitectura limpia: el agente solo orquesta, la lógica está en services/ y tools/.
"""
from langchain.agents import create_agent
from langchain_core.agents import AgentAction, AgentFinish
from typing import Union, List

from app.prompts.chatbot_solicitud_articulos_prompts import SOLICITUD_ARTICULO_AGENT_SYSTEM_PROMPT
from app.tools.chatbot_articulo_tools import ARTICULO_TOOLS


def get_estandarizacion_agent():
    """
    Crea un agente para estandarización de artículos.
    
    Responsabilidades del agente:
    - Orquestar el flujo de conversación
    - Llamar a las herramientas apropiadas
    - NO contiene lógica de negocio (está en services/)
    
    Returns:
        Agente compilado
    """
    # Usamos la sintaxis moderna con create_agent documentada en docs/core-components/Agents.md
    agent = create_agent(
        model="claude-sonnet-4-5-20250929",
        tools=ARTICULO_TOOLS,
        system_prompt=SOLICITUD_ARTICULO_AGENT_SYSTEM_PROMPT
    )
    
    return agent
