from fastapi import APIRouter, HTTPException
from app.schemas.articulo_schemas import ArticuloRequest, ArticuloResponse
from app.agents.articulo_agent import get_articulo_agent
from langchain_core.messages import HumanMessage, AIMessage
from typing import List
import uuid

router = APIRouter()

# Almacenamiento temporal de conversaciones (en producción usar Redis)
conversaciones = {}

@router.post("/estandarizar", response_model=ArticuloResponse)
async def estandarizar_articulo(request: ArticuloRequest):
    """
    Endpoint principal para estandarizar artículos mediante chat.
    Recibe descripción en lenguaje natural y retorna nombre estandarizado.
    """
    try:
        agent = get_articulo_agent()
        
        # Construir mensajes del historial si existe
        messages = []
        if request.contexto_conversacion:
            for msg in request.contexto_conversacion:
                if msg.get("rol") == "usuario":
                    messages.append(HumanMessage(content=msg.get("contenido", "")))
                else:
                    messages.append(AIMessage(content=msg.get("contenido", "")))
        
        # Agregar mensaje actual
        messages.append(HumanMessage(content=request.mensaje))
        
        # Invocar al agente
        result = agent.invoke({"messages": messages})
        
        # Extraer respuesta estructurada
        last_message = result["messages"][-1]
        
        articulo_identificado = None
        listo_para_crear = False
        action = "preguntar"
        opciones_sugeridas = []

        # Buscar si se llamó a herramientas clave en los mensajes recientes
        # Iteramos al revés para encontrar la última acción relevante
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    name = tool_call['name']
                    args = tool_call['args']
                    
                    if name == 'finalizar_estandarizacion':
                        try:
                            from app.schemas.articulo_schemas import ArticuloIdentificado
                            articulo_identificado = ArticuloIdentificado(
                                tipo=args.get('tipo'),
                                nombre_estandarizado=args.get('nombre_estandarizado'),
                                campos_extraidos=args.get('campos_extraidos', {}),
                                confianza=1.0
                            )
                            listo_para_crear = True
                            action = "crear_nuevo"
                        except Exception as parse_error:
                            print(f"Error parseando ArticuloIdentificado: {parse_error}")
                            
                    elif name == 'preguntar_con_opciones':
                        opciones_sugeridas = args.get('opciones', [])
                
                # Si encontramos alguna acción relevante, nos detenemos (prioridad a finalizar)
                if listo_para_crear or opciones_sugeridas:
                    break
        
        # --- LOGGING ---
        try:
            import json
            from datetime import datetime
            from pathlib import Path

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "usuario": request.mensaje,
                "ia_respuesta": last_message.content,
                "opciones_mostradas": opciones_sugeridas,
                "accion_sugerida": action,
                "estado_final": "listo" if listo_para_crear else "en_proceso"
            }
            
            # Guardar en logs/historial_chat_articulos.jsonl
            log_path = Path("logs/historial_chat_articulos.jsonl")
            
            # Asegurar que el directorio existe (seguridad extra)
            log_path.parent.mkdir(exist_ok=True)
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            print(f"Error guardando log: {e}")
        # ----------------

        return ArticuloResponse(
            mensaje=last_message.content,
            articulo_identificado=articulo_identificado,
            requiere_mas_info=not listo_para_crear,
            listo_para_crear=listo_para_crear,
            accion_sugerida=action,
            opciones_sugeridas=opciones_sugeridas
        )
        
    except Exception as e:
        print(f"Error en estandarización: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/validar-duplicado")
async def validar_duplicado(nombre: str):
    """
    Verifica si un nombre de artículo ya existe en Defontana.
    """
    try:
        from app.agents.articulo_agent import buscar_articulos_defontana
        
        resultados = buscar_articulos_defontana.invoke(nombre)
        
        return {
            "existe_similar": len(resultados) > 0,
            "articulos_similares": resultados
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))