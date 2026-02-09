from fastapi import APIRouter, HTTPException
from app.schemas.hse_schemas import IncidentRequest, IncidentAnalysisResponse
from app.services.llm_utils import get_hse_agent
from langchain.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
import uuid

router = APIRouter()

@router.post("/5-porques", response_model=IncidentAnalysisResponse)
async def generar_analisis(data: IncidentRequest):
    try:
        # 1. Preparar el agente (Production Ready)
        agent = get_hse_agent()
        
        # 2. Construir el contexto
        incident_context = f"""
        ANALIZAR ESTE INCIDENTE:
        ------------------------------------------------
        Tipo de Evento: {data.tipo_evento}
        Descripción: {data.descripcion}
        Acción Inmediata: {data.accion_inmediata}
        Área/Proceso: {data.area_proceso}
        Origen: {data.origen}
        Impacto: {data.impacto}
        ------------------------------------------------
        """
        
        # 3. Configuración
        # Eliminamos checkpointer y thread_id ya que es una llamada stateless (una sola vuelta)
        # config: RunnableConfig = {"configurable": {"thread_id": str(uuid.uuid4())}}

        # 4. Invocar al agente
        # Gracias a response_format, el resultado ya viene estructurado en 'structured_response'
        result = agent.invoke(
            {"messages": [HumanMessage(content=incident_context)]}
        )
        
        # 5. Extraer respuesta estructurada (Best Practice: No parsing manual)
        structured_data = result.get("structured_response")
        
        if not structured_data:
            # Fallback por seguridad si algo falla en la generación estructurada
            raise ValueError("El modelo no generó una respuesta estructurada válida.")

        return structured_data

    except Exception as e:
        print(f"Error procesando solicitud: {e}")
        raise HTTPException(status_code=500, detail=f"Error en análisis AI: {str(e)}")
