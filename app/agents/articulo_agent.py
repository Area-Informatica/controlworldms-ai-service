from langchain.agents import create_agent
from langchain.tools import tool
from app.prompts.articulo_prompts import SOLICITUD_ARTICULO_AGENT_SYSTEM_PROMPT
from typing import List, Dict, Any
import httpx
import yaml
from pathlib import Path

def load_config():
    # Asumimos que estamos en el root del proyecto
    config_path = Path("config/estandarizacion_articulos.yaml")
    if not config_path.exists():
        # Fallback si no encuentra la ruta relativa
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Tool para buscar artículos en Defontana
@tool
def buscar_articulos_defontana(termino: str) -> List[dict]:
    """
    Busca artículos existentes en Defontana que coincidan con el término.
    Retorna lista de artículos similares para evitar duplicados.
    """
    # Esta función será llamada por el agente para verificar duplicados
    # En producción, esto llamaría a la API de ControlWorldMS
    try:
        response = httpx.get(
            f"http://controlworldms.cl/api/articulos-defontana",
            params={"busqueda": termino},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("articulos", [])[:5]  # Máximo 5 resultados
    except Exception as e:
        print(f"Error buscando en Defontana: {e}")
    return []

@tool
def construir_nombre_estandar(tipo: str, atributos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construye el nombre estandarizado basado en el tipo y los atributos extraídos.
    Valida que los atributos sean correctos según la configuración.
    Args:
        tipo: El tipo de artículo (EPP, WOG, ASEO, etc.)
        atributos: Diccionario con los campos extraídos (ej: {'diametro': '1/2"', 'material': 'PVC'})
    Returns:
        Dict con 'valido', 'nombre' (si es válido), 'errores' (si hay errores)
    """
    config = load_config()
    if tipo not in config:
        return {
            "valido": False, 
            "errores": [f"Tipo de artículo '{tipo}' no encontrado en la configuración. Tipos válidos: {list(config.keys())}"]
        }
    
    config_tipo = config[tipo]
    formato = config_tipo['formato']
    campos_config = config_tipo['campos']
    
    errores = []
    valores_usados = {}
    campos_faltantes = []
    
    # Validar campos requeridos y valores
    for campo, reglas in campos_config.items():
        valor = atributos.get(campo)
        
        # Limpieza básica del valor si existe
        if valor:
            if isinstance(valor, str):
                valor = valor.strip().upper()
        
        if reglas.get('requerido') and not valor:
            errores.append(f"Falta el valor para el campo requerido: '{campo}'")
            campos_faltantes.append(campo)
            valores_usados[campo] = f"[{campo.upper()}]" # Placeholder para mostrar formato incompleto
            continue
            
        if valor:
            # Validar contra lista cerrada
            if reglas.get('tipo') == 'lista_cerrada':
                valores_permitidos = reglas.get('valores_estandar', [])
                # Intentar coincidencia exacta o normalizada
                if valor not in valores_permitidos:
                     # Sugerir el valor más cercano o reportar error
                     errores.append(f"El valor '{valor}' para '{campo}' no es válido. Valores permitidos: {valores_permitidos}")
            
            valores_usados[campo] = valor
        else:
            valores_usados[campo] = ""

    if errores:
        return {
            "valido": False, 
            "errores": errores, 
            "campos_faltantes": campos_faltantes,
            "nombre_parcial": formato.format(**valores_usados)
        }
        
    # Construir nombre final
    try:
        nombre = formato.format(**valores_usados)
        # Limpiar espacios múltiples generados por campos vacíos
        nombre = " ".join(nombre.split())
        return {"valido": True, "nombre": nombre}
    except Exception as e:
        return {"valido": False, "errores": [f"Error al formatear nombre: {str(e)}"]}

@tool
def finalizar_estandarizacion(tipo: str, nombre_estandarizado: str, campos_extraidos: dict) -> str:
    """
    Llama a esta herramienta CUANDO el artículo esté completamente estandarizado, validado y SIN errores.
    Esto señala al sistema que el proceso ha terminado exitosamente.
    """
    return "Proceso finalizado. El artículo ha sido registrado."

@tool
def consultar_reglas_tipo(tipo: str) -> dict:
    """
    Obtiene las reglas, campos y valores permitidos para un tipo de artículo.
    Útil para mostrar opciones al usuario o saber qué preguntar.
    """
    config = load_config()
    if tipo not in config:
        return {"error": f"Tipo '{tipo}' no encontrado"}
    return config[tipo]

@tool
def preguntar_con_opciones(mensaje: str, opciones: List[str]) -> str:
    """
    Se usa para hacer una pregunta al usuario PRESENTANDO una lista de opciones seleccionables (chips/botones).
    Args:
        mensaje: La pregunta (ej: "Seleccione el color")
        opciones: Lista de textos breves (ej: ["ROJO", "AZUL", "VERDE"])
    """
    return "Pregunta enviada al usuario con opciones visuales."

def get_articulo_agent():
    """
    Crea un agente para estandarización de artículos.
    Usa herramientas para buscar duplicados y validar nombres.
    """
    tools = [buscar_articulos_defontana, construir_nombre_estandar, finalizar_estandarizacion, consultar_reglas_tipo, preguntar_con_opciones]
    
    agent = create_agent(
        model="claude-sonnet-4-5-20250929",
        tools=tools,
        system_prompt=SOLICITUD_ARTICULO_AGENT_SYSTEM_PROMPT
    )
    
    return agent