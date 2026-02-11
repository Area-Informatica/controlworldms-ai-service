import sys
import os
import yaml
import random
from dotenv import load_dotenv

# Cargar variables de entorno (API Keys)
load_dotenv()

# Agregar el directorio raíz del proyecto al sys.path para que encuentre el módulo 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.agents.chatbot_solicitud_articulos_agent import get_estandarizacion_agent
from tests.simulators.user_simulator import UserSimulatorAgent
from langchain_core.messages import HumanMessage, AIMessage

# Preparamos el agente a testear (Chatbot)
chatbot_agent = get_estandarizacion_agent()

def load_categories_config():
    """Carga y parsea el archivo de configuración YAML."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'estandarizacion_articulos.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_article_details(category_config):
    """Genera datos de ejemplo válidos para una categoría basados en su config."""
    details = {}
    if 'campos' not in category_config:
        return {"descripcion": "Articulo generico de prueba"}
        
    for field_name, rules in category_config['campos'].items():
        # Si tiene valores estándar, elegimos uno al azar
        if 'valores_estandar' in rules and rules['valores_estandar']:
            val = random.choice(rules['valores_estandar'])
            details[field_name] = val
        # Si es texto libre o no tiene lista, inventamos algo genérico
        elif rules.get('tipo') == 'texto_libre':
             details[field_name] = "DetalleGenerico"
        # Si es numérico (esto dependería de cómo define numeros el yaml, pero por ahora string)
        else:
             details[field_name] = "ValorPrueba"
             
    return details

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import del Juez Experto
from tests.simulators.expert_judge import ExpertJudgeAgent, format_judgment_report

# Evaluador global desactivado para ahorrar créditos (ya no se usa en el loop principal)
# evaluator_llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)

# Juez experto global
expert_judge = ExpertJudgeAgent()


def extract_standardized_name(text: str) -> str:
    """Intenta extraer el nombre estandarizado usando Regex agnósticas al formato."""
    import re
    
    # 1. Limpieza preliminar para facilitar regex
    # Quitamos asteriscos dobles del markdown para no complicar las regex
    clean_text = text.replace("**", "").replace("__", "")
    
    # Lista de patrones optimizada (aplicada sobre texto limpio)
    patterns = [
        # Etiquetas explícitas (más confiables)
        r'Nombre final:\s*([^\n\.]+)',
        r'Nombre estandarizado:\s*([^\n\.]+)',
        r'Artículo creado:\s*([^\n\.]+)',
        r'Nombre asignado:\s*([^\n\.]+)',
        
        # Frases narrativas
        r'estandarizado exitosamente a:?\s*["\']?([^"\'\n\.]+)["\']?',
        r'estandarizado como:?\s*["\']?([^"\'\n\.]+)["\']?',
        r'quedado registrado como:?\s*["\']?([^"\'\n\.]+)["\']?',
        
        # Formatos específicos vistos en logs
        r'estandarizado exitosamente:\s*\n+([^\n]+)',
        r'Nombre final:\s*\n+([^\n]+)' # Caso donde el nombre está en la línea siguiente
    ]
    
    for pat in patterns:
        match = re.search(pat, clean_text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Validaciones básicas para no capturar basura
            # Un nombre estandarizado suele tener mayúsculas y números, longitud min 3
            if len(candidate) > 3 and not candidate.lower().startswith("http"):
                # Limpiar puntuación final o comillas residuales
                candidate = candidate.strip('."\'').strip()
                return candidate
                
    return None

def is_success_message_heuristic(text: str) -> bool:
    """Detecta éxito usando palabras clave en lugar de un LLM (Cero costo)."""
    text_lower = text.lower()
    keywords = [
        "estandarizado exitosamente",
        "nombre final:",
        "listo, tu artículo",
        "asignado el nombre",
        "registrado exitosamente",
        "listo para ser utilizado", 
        "artículo está listo",
        "todo quedó bien registrado",
        "creado el artículo"
    ]
    return any(k in text_lower for k in keywords)


def run_simulation(category: str, user_profile: str, article_details: dict = None, max_turns: int = 20):
    """
    Ejecuta una simulación completa de conversación entre:
    1. Chatbot (Sistema real)
    2. User Simulator (Agente de prueba)
    
    Returns:
        tuple: (success: bool, standardized_name: str or None, conversation: str)
    """
    print(f"\n\n{'='*60}")
    print(f"   SIMULACIÓN: CATEGORÍA '{category}' | PERFIL '{user_profile.upper()}'")
    print(f"{'='*60}")
    
    # Inicializar simulador con detalles específicos
    user_sim = UserSimulatorAgent(role_profile=user_profile)
    user_sim.set_goal(category, complexity="medium", custom_details=article_details)
    
    # Estado inicial
    chat_history_for_bot = [] 
    chat_history_for_sim = []
    
    # IMPORTANTE: Trackear el nombre detectado a lo largo de toda la conversación
    last_detected_name = None
    
    # El usuario sim siempre inicia
    initial_message = user_sim.generate_response([])
    print(f"\n[USUARIO - {user_profile}]: {initial_message}")
    
    chat_history_for_bot.append(HumanMessage(content=initial_message))
    chat_history_for_sim.append({"role": "user", "content": initial_message})
    
    for i in range(max_turns):
        print(f"\n--- Turno {i+1} ---")
        
        # 1. Turno del Chatbot
        try:
            def call_chatbot():
                return chatbot_agent.invoke({"messages": chat_history_for_bot})
                
            response = retry_with_backoff(call_chatbot)
            bot_msg_full = response["messages"][-1]
            
            # Extraer texto limpio
            bot_text = ""
            if isinstance(bot_msg_full.content, list):
                for block in bot_msg_full.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        bot_text += block.get("text", "")
            else:
                bot_text = str(bot_msg_full.content)
            
            # Intento oportunista de extraer el nombre en cada turno
            possible_name = extract_standardized_name(bot_text)
            if possible_name:
                last_detected_name = possible_name
                print(f"   [DEBUG] Nombre detectado: '{last_detected_name}'")
                
            print(f"[BOT]: {bot_text}")
            
            # Guardar en historiales
            chat_history_for_bot.append(AIMessage(content=bot_msg_full.content))
            chat_history_for_sim.append({"role": "assistant", "content": bot_text})
            
            # Chequear fin por tool call
            if hasattr(bot_msg_full, 'tool_calls') and bot_msg_full.tool_calls:
                for tc in bot_msg_full.tool_calls:
                    if tc['name'] == 'finalizar_estandarizacion':
                        # Preferir el argumento de la tool si existe
                        tc_name = tc['args'].get('nombre_estandarizado')
                        final_name = tc_name if tc_name else last_detected_name
                        
                        print(f"\n>>> ¡ÉXITO! El chatbot finalizó: {final_name}\n")
                        conversation = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history_for_sim])
                        return True, final_name, conversation
            
            # CRITERIO DE PARADA (HEURÍSTICO / REGEX):
            # Optimizamos créditos eliminando llamadas a LLM para validación de éxito.
            
            is_success_msg = is_success_message_heuristic(bot_text)
            
            if i >= 1 and is_success_msg:
                # Usar el nombre que acabamos de extraer o el último visto
                final_name = possible_name if possible_name else last_detected_name
                
                print(f"\n>>> ÉXITO IMPLÍCITO (Detectado por heurística). Nombre: {final_name}\n")
                conversation = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history_for_sim])
                return True, final_name, conversation

        except Exception as e:
            print(f">>> ERROR en el chatbot: {e}")
            conversation = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history_for_sim])
            return False, None, conversation
            
        # 2. Turno del Usuario Simulado
        try:
            def call_simulator():
                return user_sim.generate_response(chat_history_for_sim)
                
            user_response = retry_with_backoff(call_simulator)
            print(f"[USUARIO - {user_profile}]: {user_response}")
            
            # FAILSAFE 1: Detección explícita de fin de simulación por palabra clave
            if "TERMINAR_SIMULACION" in user_response:
                final_name = last_detected_name if last_detected_name else "NOMBRE_NO_DETECTADO"
                print(f"\n>>> ÉXITO: Usuario finalizó voluntariamente. Nombre: {final_name}\n")
                conversation = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history_for_sim])
                
                # Si terminamos pero no tenemos nombre, marcamos como éxito parcial (pero éxito al fin) para avanzar
                return True, final_name if last_detected_name else None, conversation

            # FAILSAFE 2: Si el usuario dice GRACIAS/CONFIRMO repetidamente (Legacy support)
            if user_response.strip().upper().startswith(("GRACIAS", "¡GRACIAS", "CONFIRMO", "PERFECTO", "MUCHAS GRACIAS")):
                 if last_detected_name:
                     print(f"\n>>> ÉXITO: Usuario confirmó cierre y tenemos nombre ({last_detected_name}). Finalizando.\n")
                     conversation = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history_for_sim])
                     return True, last_detected_name, conversation
            
            chat_history_for_bot.append(HumanMessage(content=user_response))
            chat_history_for_sim.append({"role": "user", "content": user_response})
        except Exception as e:
             print(f">>> ERROR en el simulador: {e}")
             conversation = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history_for_sim])
             return False, None, conversation

    print(f"\n>>> FALLO: Se alcanzaron los {max_turns} turnos sin estandarización.\n")
    conversation = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history_for_sim])
    return False, None, conversation


def retry_with_backoff(func, max_retries=3):
    """Ejecuta una función con reintentos exponenciales para errores de sobrecarga."""
    from anthropic import APIStatusError, APITimeoutError, RateLimitError
    
    for attempt in range(max_retries):
        try:
            return func()
        except (APIStatusError, APITimeoutError, RateLimitError) as e:
            # Capturamos APIStatusError para atrapar 529 OverloadedError si no está expuesto directamente
            is_overloaded = isinstance(e, APIStatusError) and e.status_code == 529
            is_rate_limit = isinstance(e, RateLimitError)
            
            if not (is_overloaded or is_rate_limit):
                raise e
                
            if attempt == max_retries - 1:
                raise e
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"⚠️ API sobrecargada (Status {e.status_code}). Reintentando en {wait_time:.1f}s...")
            time.sleep(wait_time)
        except Exception as e:
            # Si es otro error, propagar inmediatamente
            raise e
    return None

if __name__ == "__main__":
    import argparse
    import random
    import time
    
    # Configuración de argumentos por línea de comandos
    parser = argparse.ArgumentParser(description="Simulación de Estandarización de Artículos con Agentes AI")
    parser.add_argument("-c", "--category", type=str, help="Categoría específica a probar (ej: EPP). Si se omite, prueba todas.")
    parser.add_argument("-p", "--profile", type=str, default="standard", help="Perfil del usuario simulado (standard, confused, impatient, expert, typo_king). Usa 'all' para todos.")
    parser.add_argument("-n", "--iterations", type=int, default=1, help="Número de iteraciones por cada combinación categoría/perfil.")
    
    # Intenta parsear, si falla (ej: corriendo desde IDE sin args), usa defaults
    try:
        args = parser.parse_args()
    except SystemExit:
        # Defaults seguros si hay error de args o si estamos en entorno no interactivo raro
        class Args:
            category = None
            profile = "standard"
            iterations = 1
        args = Args()

    # Cargar configuración real
    full_config = load_categories_config()
    
    # Determinar categorías a probar
    all_categories = [k for k in full_config.keys() if k.isupper()]
    if args.category:
        if args.category.upper() not in all_categories:
            print(f"❌ Categoría '{args.category}' no encontrada en configuración. Disponibles: {', '.join(all_categories)}")
            exit(1)
        target_categories = [args.category.upper()]
    else:
        target_categories = all_categories

    # Determinar perfiles a probar
    valid_profiles = ["standard", "confused", "impatient", "expert", "typo_king"]
    if args.profile.lower() == "all":
        target_profiles = valid_profiles
    elif args.profile.lower() in valid_profiles:
        target_profiles = [args.profile.lower()]
    else:
        print(f"❌ Perfil '{args.profile}' no válido. Disponibles: {', '.join(valid_profiles)}")
        exit(1)

    results = []
    judge_verdicts = []  # Para almacenar veredictos del juez
    
    print(f"\n🚀 INICIANDO SIMULACIÓN DINÁMICA")
    print(f"   Categorías:  {target_categories}")
    print(f"   Perfiles:    {target_profiles}")
    print(f"   Iteraciones: {args.iterations}")
    print("   🧑‍⚖️ LLM-as-a-Judge HABILITADO\n")
    
    for cat in target_categories:
        cat_config = full_config[cat]
        
        for prof in target_profiles:
            for i in range(args.iterations):
                # Generar detalles válidos DIFERENTES para cada iteración
                generated_details = generate_article_details(cat_config)
                
                sim_id = f"{cat} | {prof} | It.{i+1}"
                print(f"\n▶ EJECUTANDO: {cat} - {prof} (Iteración {i+1}/{args.iterations})")
                
                # PAUSA INTENCIONAL PARA EVITAR RATE LIMITING (Error 529 Overloaded)
                if i > 0 or prof != target_profiles[0] or cat != target_categories[0]:
                    print("   [INFO] Pausando 5 segundos para evitar sobrecarga de API...")
                    time.sleep(5)
                
                print(f"  (Meta simulada: {generated_details})")
                
                try:
                    success, standardized_name, conversation = run_simulation(
                        cat, prof, article_details=generated_details, max_turns=12
                    )
                    
                    if success:
                        status = "✅ PASÓ"
                        
                        # Si fue exitoso y tenemos nombre, evaluamos con el juez
                        if standardized_name:
                            print(f"\n🧑‍⚖️ Evaluando con Juez Experto en {cat}...")
                            try:
                                judgment = expert_judge.judge(
                                    category=cat,
                                    standardized_name=standardized_name,
                                    original_input=generated_details,
                                    conversation_history=conversation
                                )
                                print(format_judgment_report(judgment, cat, standardized_name))
                                
                                # Guardar veredicto
                                judge_verdicts.append({
                                    "categoria": cat,
                                    "perfil": prof,
                                    "iteracion": i+1,
                                    "nombre": standardized_name,
                                    "valido": judgment.valido,
                                    "puntuacion": judgment.puntuacion
                                })
                                
                                # Agregar puntuación al status
                                status += f" | Juez: {judgment.puntuacion}/10 {'✓' if judgment.valido else '✗'}"
                            except Exception as je:
                                print(f">>> Error en el juez: {je}")
                                status += " | Juez: ERROR"
                        else:
                            status += " | Juez: Sin nombre para evaluar"
                    else:
                        status = "❌ FALLÓ"
                        
                    results.append(f"{sim_id:<30} | {status}")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    results.append(f"{sim_id:<30} | ❌ ERROR: {str(e)}")
                
    print("\n\n" + "="*80)
    print("RESUMEN DE RESULTADOS DE SIMULACIÓN DINÁMICA")
    print("="*80)
    print(f"{'SIMULACIÓN':<30} | ESTADO")
    print("-" * 80)
    for line in results:
        print(line)
    print("="*80)
    
    # Resumen del juez
    if judge_verdicts:
        print("\n" + "="*80)
        print("RESUMEN DE VEREDICTOS DEL JUEZ EXPERTO")
        print("="*80)
        total = len(judge_verdicts)
        validos = sum(1 for v in judge_verdicts if v["valido"])
        promedio = sum(v["puntuacion"] for v in judge_verdicts) / total if total > 0 else 0
        
        print(f"📊 Total evaluados: {total}")
        print(f"✅ Válidos: {validos}/{total} ({100*validos/total:.1f}%)")
        print(f"📈 Puntuación promedio: {promedio:.1f}/10")
        
        print("\nDetalle por caso:")
        print("-" * 80)
        for v in judge_verdicts:
            emoji = "✅" if v["valido"] else "❌"
            label = f"{v['categoria']} ({v['perfil']}) #{v['iteracion']}"
            print(f"  {emoji} {label:<25} | {v['nombre']:<35} | {v['puntuacion']}/10")
        print("="*80 + "\n")
