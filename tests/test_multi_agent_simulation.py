import pytest
from app.agents.chatbot_solicitud_articulos_agent import get_estandarizacion_agent
from tests.simulators.user_simulator import UserSimulatorAgent
from langchain_core.messages import HumanMessage, AIMessage

# Preparamos el agente a testear (Chatbot)
chatbot_agent = get_estandarizacion_agent()

def run_simulation(category: str, user_profile: str, max_turns: int = 15):
    """
    Ejecuta una simulación completa de conversación entre:
    1. Chatbot (Sistema real)
    2. User Simulator (Agente de prueba)
    """
    print(f"\n\n{'='*60}")
    print(f"   SIMULACIÓN: CATEGORÍA '{category}' | PERFIL '{user_profile.upper()}'")
    print(f"{'='*60}")
    
    # Inicializar simulador
    user_sim = UserSimulatorAgent(role_profile=user_profile)
    user_sim.set_goal(category)
    
    # Estado inicial
    chat_history_for_bot = [] # LangChain objects
    chat_history_for_sim = [] # Dict objects
    
    # El usuario sim siempre inicia
    initial_message = user_sim.generate_response([])
    print(f"\n[USUARIO - {user_profile}]: {initial_message}")
    
    chat_history_for_bot.append(HumanMessage(content=initial_message))
    chat_history_for_sim.append({"role": "user", "content": initial_message})
    
    for i in range(max_turns):
        print(f"\n--- Turno {i+1} ---")
        
        # 1. Turno del Chatbot
        try:
            response = chatbot_agent.invoke({"messages": chat_history_for_bot})
            bot_msg_full = response["messages"][-1]
            
            # Extraer texto limpio
            bot_text = ""
            if isinstance(bot_msg_full.content, list):
                for block in bot_msg_full.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        bot_text += block.get("text", "")
            else:
                bot_text = str(bot_msg_full.content)
                
            print(f"[BOT]: {bot_text}")
            
            # Guardar en historiales
            chat_history_for_bot.append(AIMessage(content=bot_msg_full.content))
            chat_history_for_sim.append({"role": "assistant", "content": bot_text})
            
            # Chequear si el bot terminó (detectando tool call de finalizar)
            if hasattr(bot_msg_full, 'tool_calls') and bot_msg_full.tool_calls:
                for tc in bot_msg_full.tool_calls:
                    if tc['name'] == 'finalizar_estandarizacion':
                        print(f"\n>>> ¡ÉXITO! El chatbot finalizó: {tc['args'].get('nombre_estandarizado')}\n")
                        return True
        except Exception as e:
            print(f">>> ERROR en el chatbot: {e}")
            return False
            
        # 2. Turno del Usuario Simulado
        try:
            user_response = user_sim.generate_response(chat_history_for_sim)
            print(f"[USUARIO - {user_profile}]: {user_response}")
            
            chat_history_for_bot.append(HumanMessage(content=user_response))
            chat_history_for_sim.append({"role": "user", "content": user_response})
        except Exception as e:
             print(f">>> ERROR en el simulador: {e}")
             return False

    print(f"\n>>> FALLO: Se alcanzaron los {max_turns} turnos sin estandarización.\n")
    return False

# -------------------------------------------------------------------------
# TESTS DE EPP (ACTIVOS)
# -------------------------------------------------------------------------

def test_epp_standard():
    """EPP: Usuario que coopera normalmente"""
    assert run_simulation("EPP", "standard") is True

def test_epp_confused():
    """EPP: Usuario que no sabe mucho (costoso en turnos)"""
    assert run_simulation("EPP", "confused") is True

def test_epp_expert():
    """EPP: Usuario experto (debería ser rápido)"""
    assert run_simulation("EPP", "expert", max_turns=6) is True

# -------------------------------------------------------------------------
# TESTS DE WOG (COMENTADOS/DESACTIVADOS)
# -------------------------------------------------------------------------

# def test_wog_standard():
#     assert run_simulation("WOG", "standard") is True

# def test_wog_confused():
#     assert run_simulation("WOG", "confused") is True

# def test_wog_expert():
#     assert run_simulation("WOG", "expert", max_turns=6) is True

# -------------------------------------------------------------------------
# TESTS DE ELECTRICIDAD (COMENTADOS/DESACTIVADOS)
# -------------------------------------------------------------------------

# def test_elec_standard():
#     assert run_simulation("ELECTRICIDAD", "standard") is True

# def test_elec_confused():
#     assert run_simulation("ELECTRICIDAD", "confused") is True

# def test_elec_expert():
#     assert run_simulation("ELECTRICIDAD", "expert", max_turns=6) is True


if __name__ == "__main__":
    # Ejecución manual: python tests/test_multi_agent_simulation.py
    print("Ejecutando simulaciones EPP...")
    test_epp_standard()
    test_epp_confused()
    test_epp_expert()
