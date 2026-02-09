import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def get_llm_model(model_name: str = "claude-sonnet-4-5-20250929", temperature: float = 0.1) -> ChatAnthropic:
    """
    Retorna una instancia de ChatAnthropic configurada.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL ERROR: ANTHROPIC_API_KEY no encontrada en variables de entorno.")

    return ChatAnthropic(
        api_key=api_key,
        model=model_name,
        temperature=temperature
    )




