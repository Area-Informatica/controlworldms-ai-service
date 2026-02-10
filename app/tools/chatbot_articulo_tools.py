"""
Herramientas (tools) para el agente de estandarización de artículos.
Cada tool es un wrapper delgado que llama a los servicios correspondientes.
"""
from langchain.tools import tool
from typing import List, Dict, Any
import httpx

from app.services.chatbot_estandarizacion_articulos.categorias_service import (
    obtener_categorias,
    obtener_reglas_categoria,
    inferir_categoria as _inferir_categoria,
)
from app.services.chatbot_estandarizacion_articulos.normalizacion_utils import normalizar_valor


@tool
def buscar_articulos_defontana(termino: str) -> List[dict]:
    """
    Busca artículos existentes en Defontana que coincidan con el término.
    Retorna lista de artículos similares para evitar duplicados.
    """
    try:
        response = httpx.get(
            "http://controlworldms.cl/api/articulos-defontana",
            params={"busqueda": termino},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("articulos", [])[:5]
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
        atributos: Diccionario con los campos extraídos
    
    Returns:
        Dict con 'valido', 'nombre' (si es válido), 'errores' (si hay errores)
    """
    config_tipo = obtener_reglas_categoria(tipo)
    
    if not config_tipo:
        categorias = obtener_categorias()
        tipos_validos = [c["id"] for c in categorias]
        return {
            "valido": False, 
            "errores": [f"Tipo '{tipo}' no encontrado. Válidos: {tipos_validos}"]
        }
    
    formato = config_tipo['formato']
    campos_config = config_tipo['campos']
    
    errores = []
    valores_usados = {}
    campos_faltantes = []
    
    for campo, reglas in campos_config.items():
        valor = atributos.get(campo, "")
        
        # Normalizar valor usando el servicio
        if valor:
            valor = normalizar_valor(valor, campo)
        
        # Validar campo requerido
        if reglas.get('requerido') and not valor:
            errores.append(f"Campo requerido faltante: '{campo}'")
            campos_faltantes.append(campo)
            valores_usados[campo] = f"[{campo.upper()}]"
            continue
            
        # Validar contra lista cerrada
        if valor and reglas.get('tipo') == 'lista_cerrada':
            valores_permitidos = reglas.get('valores_estandar', [])
            if valor not in valores_permitidos:
                errores.append(f"'{valor}' no válido para '{campo}'. Permitidos: {valores_permitidos}")
        
        valores_usados[campo] = valor if valor else ""

    if errores:
        return {
            "valido": False, 
            "errores": errores, 
            "campos_faltantes": campos_faltantes,
            "nombre_parcial": formato.format(**valores_usados)
        }
    
    try:
        nombre = " ".join(formato.format(**valores_usados).split())
        return {"valido": True, "nombre": nombre}
    except Exception as e:
        return {"valido": False, "errores": [f"Error formateando: {str(e)}"]}


@tool
def inferir_categoria(descripcion_articulo: str) -> Dict[str, Any]:
    """
    Analiza la descripción de un artículo e infiere la categoría más probable.
    Útil cuando el usuario no sabe qué categoría usar.
    
    Args:
        descripcion_articulo: Texto libre describiendo el artículo
    
    Returns:
        Dict con categoria_inferida, confianza, palabras_detectadas, alternativas
    """
    resultado = _inferir_categoria(descripcion_articulo)
    return {
        "categoria_inferida": resultado.categoria_inferida,
        "descripcion": resultado.descripcion,
        "confianza": resultado.confianza,
        "palabras_detectadas": resultado.palabras_detectadas,
        "alternativas": resultado.alternativas
    }


@tool
def listar_categorias() -> List[Dict[str, str]]:
    """
    Retorna la lista de todas las categorías disponibles con sus descripciones.
    Útil para mostrar al usuario al inicio de la conversación.
    """
    return obtener_categorias()


@tool
def consultar_reglas_tipo(tipo: str) -> dict:
    """
    Obtiene las reglas, campos y valores permitidos para un tipo de artículo.
    Útil para mostrar opciones al usuario o saber qué preguntar.
    """
    reglas = obtener_reglas_categoria(tipo)
    if not reglas:
        return {"error": f"Tipo '{tipo}' no encontrado"}
    return reglas


@tool
def finalizar_estandarizacion(tipo: str, nombre_estandarizado: str, campos_extraidos: dict) -> str:
    """
    Señala que el artículo está completamente estandarizado y validado.
    Llama a esta herramienta cuando el proceso termine exitosamente.
    """
    return "Proceso finalizado. El artículo ha sido registrado."


@tool
def preguntar_con_opciones(mensaje: str, opciones: List[str], permitir_otro_valor: bool = True) -> str:
    """
    Presenta una pregunta al usuario con opciones seleccionables.
    
    Args:
        mensaje: La pregunta a mostrar
        opciones: Lista de opciones disponibles
        permitir_otro_valor: Si el usuario puede escribir un valor personalizado
    """
    return "Pregunta enviada al usuario con opciones visuales."


# Exportar todas las tools para facilitar la importación
ARTICULO_TOOLS = [
    buscar_articulos_defontana,
    construir_nombre_estandar,
    inferir_categoria,
    listar_categorias,
    consultar_reglas_tipo,
    finalizar_estandarizacion,
    preguntar_con_opciones,
]
