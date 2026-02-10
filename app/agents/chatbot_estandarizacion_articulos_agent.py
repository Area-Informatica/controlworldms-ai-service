"""
Agente de estandarización de artículos.
Arquitectura limpia: el agente solo orquesta, la lógica está en services/ y tools/.
"""
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_anthropic import ChatAnthropic

from app.prompts.chatbot_estandarizacion_articulos_prompts import SOLICITUD_ARTICULO_AGENT_SYSTEM_PROMPT
from app.tools.chatbot_articulo_tools import ARTICULO_TOOLS


def get_estandarizacion_agent() -> AgentExecutor:
    """
    Crea un agente para estandarización de artículos.
    
    Responsabilidades del agente:
    - Orquestar el flujo de conversación
    - Llamar a las herramientas apropiadas
    - NO contiene lógica de negocio (está en services/)
    
    Returns:
        AgentExecutor configurado con las herramientas de estandarización
    """
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        temperature=0,
        max_tokens=1024,
        timeout=None,
        max_retries=2,
    )

    agent = create_tool_calling_agent(
        llm=llm,
        tools=ARTICULO_TOOLS,
        prompt=SOLICITUD_ARTICULO_AGENT_SYSTEM_PROMPT
    )
    
    return AgentExecutor(
        agent=agent, 
        tools=ARTICULO_TOOLS, 
        verbose=True
    )
