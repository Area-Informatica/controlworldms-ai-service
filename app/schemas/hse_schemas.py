from pydantic import BaseModel, Field
from typing import Optional, Any

class IncidentRequest(BaseModel):
    correlativo: Optional[str] = None
    tipo_evento: str
    descripcion: str
    clausula: Optional[str] = None
    fecha_levantamiento: Optional[str] = None
    accion_inmediata: str = "No especificada"
    area_proceso: str
    origen: str
    impacto: str
    user_levantamiento: Optional[str] = None

class IncidentAnalysisResponse(BaseModel):
    analisis_5_porque: str = Field(description="Explicación detallada de la secuencia de los 5 porqués, paso a paso.")
    causa_raiz: str = Field(description="La causa raíz fundamental identificada tras el análisis.")
