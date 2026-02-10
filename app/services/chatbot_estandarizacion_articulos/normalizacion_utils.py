"""
Utilidades de normalización de texto para artículos.
Centraliza toda la lógica de limpieza y estandarización de valores.
"""
import re
from typing import Dict, Optional

# Mapeo de tallas: valor sucio -> valor estándar
TALLAS_NORMALIZE: Dict[str, str] = {
    "SMALL": "S", "MEDIUM": "M", "LARGE": "L", "EXTRA LARGE": "XL",
    "CHICA": "S", "MEDIANA": "M", "GRANDE": "L", "EXTRA GRANDE": "XL",
    "CHICO": "S", "MEDIANO": "M", "XXLARGE": "XXL", "XXXLARGE": "XXXL",
    "T/S": "S", "T/M": "M", "T/L": "L", "T/XL": "XL",
    "T-S": "S", "T-M": "M", "T-L": "L", "T-XL": "XL",
    "TS": "S", "TM": "M", "TL": "L", "TXL": "XL",
}

# Valores que significan "sin información"
SIN_INFO_VALORES = ["SIN TALLA", "NO APLICA", "N/A", "NINGUNA", "SIN COLOR", "SIN MARCA", "NA", "-", ""]

# Prefijos redundantes a eliminar
PREFIJOS_REDUNDANTES = ["MARCA ", "TALLA ", "COLOR ", "MODELO ", "TIPO ", "SIZE ", "T/", "T-", "T."]


def normalizar_talla(valor: str) -> str:
    """Normaliza valores de talla a formato estándar."""
    valor = valor.strip().upper()
    return TALLAS_NORMALIZE.get(valor, valor)


def normalizar_unidades(texto: str) -> str:
    """Normaliza unidades de medida a formato compacto."""
    # Litros: "20 LITROS", "20 LTS", "20L" -> "20L"
    texto = re.sub(r'(\d+)\s*(LITROS?|LTS?)\b', r'\1L', texto)
    # Kilogramos: "25 KILOS", "25 KGS", "25KG" -> "25KG"
    texto = re.sub(r'(\d+)\s*(KILOS?|KGS?)\b', r'\1KG', texto)
    # Pulgadas: "7 PULGADAS", "7 PULG" -> "7"
    texto = re.sub(r'(\d+)\s*(PULGADAS?|PULG\.?)\b', r'\1"', texto)
    # Metros: "6 METROS", "6 MTS" -> "6M"
    texto = re.sub(r'(\d+)\s*(METROS?|MTS?)\b', r'\1M', texto)
    # Milímetros: "50 MILIMETROS" -> "50MM"
    texto = re.sub(r'(\d+)\s*(MILIMETROS?)\b', r'\1MM', texto)
    return texto


def limpiar_codigo_sku(texto: str) -> str:
    """Elimina códigos SKU embebidos en el texto."""
    texto = re.sub(r'\s*SKU\s*\d+', '', texto)
    texto = re.sub(r'\s*COD\.?\s*\d+', '', texto)
    return texto


def eliminar_prefijos_redundantes(texto: str) -> str:
    """Elimina prefijos redundantes como 'MARCA ', 'TALLA ', etc."""
    for prefix in PREFIJOS_REDUNDANTES:
        if texto.startswith(prefix):
            texto = texto[len(prefix):].strip()
    return texto


def normalizar_valor(valor: str, campo: Optional[str] = None) -> str:
    """
    Normaliza un valor de campo aplicando todas las reglas de limpieza.
    
    Args:
        valor: El valor a normalizar
        campo: Nombre del campo (opcional, para reglas específicas)
    
    Returns:
        Valor normalizado en mayúsculas
    """
    if not valor or not isinstance(valor, str):
        return ""
    
    valor = valor.strip().upper()
    
    # 1. Eliminar prefijos redundantes
    valor = eliminar_prefijos_redundantes(valor)
    
    # 2. Normalización específica de tallas
    if campo == "talla":
        valor = normalizar_talla(valor)
    
    # 3. Manejar valores "sin info"
    if valor in SIN_INFO_VALORES:
        if campo == "talla":
            return "UNICA"
        return ""
    
    # 4. Normalizar unidades
    valor = normalizar_unidades(valor)
    
    # 5. Limpiar SKUs
    valor = limpiar_codigo_sku(valor)
    
    # 6. Limpiar espacios múltiples
    valor = ' '.join(valor.split())
    
    return valor
