from fastapi import APIRouter, HTTPException
from app.schemas.chatbot_solicitud_articulos_schemas import ArticuloRequest, ArticuloResponse
from app.agents.chatbot_solicitud_articulos_agent import get_estandarizacion_agent
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
        agent = get_estandarizacion_agent()
        
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
        
        # Corrección para cuando Claude retorna una lista de bloques (text + tool_use)
        response_text = ""
        if isinstance(last_message.content, list):
            for block in last_message.content:
                if isinstance(block, dict) and block.get("type") == "text":
                    response_text += block.get("text", "")
        else:
            response_text = str(last_message.content)

        # Fallback para mensajes vacíos (ej. solo tool calls)
        if not response_text or not response_text.strip():
            # Si hay tool calls en el último mensaje
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                 # Check if the tool call is preguntar_con_opciones specificially to give a better message
                is_question = any(tc.get('name') == 'preguntar_con_opciones' for tc in last_message.tool_calls)
                if is_question:
                     # This usually means options are provided but no text. 
                     # We can default to a generic prompt since the UI will show options.
                     response_text = "Por favor selecciona una opción:"
                else:
                    response_text = "Procesando información..."
            else:
                # If no content and no tool calls in last message, check previous message for tools
                # Sometimes the chain ends on a ToolMessage, not AIMessage.
                found_tool_output = False
                if len(result["messages"]) >= 2:
                    second_last = result["messages"][-2]
                    # If the second to last was a tool call, and last message is empty, 
                    # maybe the model stopped unexpectedly.
                    if hasattr(second_last, 'tool_calls') and second_last.tool_calls:
                         response_text = "Evaluando respuesta..."
                         found_tool_output = True
                
                if not found_tool_output:
                     response_text = "..."

        articulo_identificado = None
        listo_para_crear = False
        action = "preguntar"
        opciones_sugeridas = []
        permitir_input_abierto = True

        # Buscar si se llamó a herramientas clave en los mensajes recientes
        # Iteramos al revés para encontrar la última acción relevante
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    name = tool_call['name']
                    args = tool_call['args']
                    
                    if name == 'finalizar_estandarizacion':
                        try:
                            from app.schemas.chatbot_solicitud_articulos_schemas import ArticuloIdentificado
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
                        permitir_input_abierto = args.get('permitir_otro_valor', True)
                
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
                "contexto_previo": request.contexto_conversacion,
                "ia_respuesta": response_text,
                "opciones_mostradas": opciones_sugeridas,
                "permitir_input_abierto": permitir_input_abierto,
                "accion_sugerida": action,
                "estado_final": "listo" if listo_para_crear else "en_proceso"
            }
            
            # Guardar en logs/historial_chatbot_solicitud_articulos.jsonl
            log_path = Path("logs/historial_chatbot_solicitud_articulos.jsonl")
            
            # Asegurar que el directorio existe (seguridad extra)
            log_path.parent.mkdir(exist_ok=True)
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            print(f"Error guardando log: {e}")
        # ----------------

        return ArticuloResponse(
            mensaje=response_text,
            articulo_identificado=articulo_identificado,
            requiere_mas_info=not listo_para_crear,
            listo_para_crear=listo_para_crear,
            accion_sugerida=action,
            opciones_sugeridas=opciones_sugeridas,
            permitir_input_abierto=permitir_input_abierto
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
        from app.tools.chatbot_articulo_tools import buscar_articulos_defontana
        
        resultados = buscar_articulos_defontana.invoke(nombre)
        
        return {
            "existe_similar": len(resultados) > 0,
            "articulos_similares": resultados
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))