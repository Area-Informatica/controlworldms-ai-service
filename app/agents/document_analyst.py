from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser

# Usamos un modelo rápido y barato para esta tarea de extracción pura
llm_analyst = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)

ANALYSIS_PROMPT = """
Eres un ANALISTA TÉCNICO experto en suministros industriales.
Tu tarea es leer el siguiente contenido extraído de un documento (ficha técnica, cotización, manual) 
y extraer ÚNICAMENTE las especificaciones técnicas relevantes para catalogar un artículo.

# OBJETIVO
Generar un resumen CONCISO y ESTRUCTURADO de los atributos técnicos.
Ignora: términos legales, direcciones, teléfonos, marketing, introducciones.

# FORMATO DE SALIDA
Producto: [Nombre principal]
Categoría Sugerida: [EPP, FERRETERIA, HERRAMIENTAS, etc]
Especificaciones:
- [Atributo]: [Valor]
- [Atributo]: [Valor]

# TEXTO DEL DOCUMENTO:
{text}
"""

def analyze_document_content(text: str) -> str:
    """
    Analiza texto crudo y retorna un resumen técnico estructurado
    usando un modelo ligero (Haiku) para ahorrar costos.
    """
    # Si el texto es muy largo, lo recortamos (aprox 2000 tokens de palabras)
    # para evitar errores de contexto y gastos innecesarios.
    truncated_text = text[:8000] 
    
    prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)
    chain = prompt | llm_analyst | StrOutputParser()
    
    return chain.invoke({"text": truncated_text})
