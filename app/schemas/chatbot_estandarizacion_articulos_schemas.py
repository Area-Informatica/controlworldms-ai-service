from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum

class TipoArticulo(str, Enum):
    EPP = "EPP"
    WOG = "WOG"
    COMBUSTIBLE = "COMBUSTIBLE"
    ASEO = "ASEO"
    OFICINA = "OFICINA"
    CONSTRUCCION = "CONSTRUCCION"
    VEHICULOS = "VEHICULOS"
    ELECTRICIDAD = "ELECTRICIDAD"
    HERRAMIENTAS = "HERRAMIENTAS"
    EQUIPOS = "EQUIPOS"
    COMPUTACIONAL = 'COMPUTACIONAL'

class ArticuloRequest(BaseModel):
    """Request del usuario en lenguaje natural"""
    mensaje: str = Field(description="Descripción del artículo que necesita el usuario")
    contexto_conversacion: Optional[List[dict]] = Field(default=None, description="Historial de la conversación")

class ArticuloIdentificado(BaseModel):
    """Artículo extraído y estandarizado"""
    tipo: TipoArticulo
    nombre_estandarizado: str = Field(description="Nombre generado según el estándar definido")
    campos_extraidos: dict = Field(description="Campos específicos del tipo de artículo")
    campos_faltantes: List[str] = Field(default=[], description="Campos que aún faltan por definir")
    confianza: float = Field(ge=0, le=1, description="Nivel de confianza de la clasificación")

class ArticuloExistenteDefontana(BaseModel):
    """Artículo encontrado en Defontana"""
    codigo: str
    nombre: str
    similitud: float = Field(ge=0, le=1, description="Porcentaje de similitud con lo solicitado")

class ArticuloResponse(BaseModel):
    """Respuesta del agente"""
    mensaje: str = Field(description="Mensaje para mostrar al usuario")
    articulo_identificado: Optional[ArticuloIdentificado] = None
    articulos_similares: List[ArticuloExistenteDefontana] = Field(default=[])
    requiere_mas_info: bool = Field(default=False, description="Si necesita más información del usuario")
    pregunta_siguiente: Optional[str] = Field(default=None, description="Pregunta a hacer si falta info")
    opciones_sugeridas: List[str] = Field(default=[], description="Lista de opciones válidas para facilitar la selección al usuario")
    permitir_input_abierto: bool = Field(default=True, description="Si true, el usuario puede ingresar texto libre además de las opciones")
    listo_para_crear: bool = Field(default=False, description="Si el artículo está listo para crear en Defontana")
    accion_sugerida: Literal["usar_existente", "crear_nuevo", "preguntar"] = "preguntar"