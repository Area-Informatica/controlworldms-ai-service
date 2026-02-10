from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import random

class UserSimulatorAgent:
    def __init__(self, role_profile: str = "standard"):
        self.llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0.7)
        self.role_profile = role_profile
        self.goal = ""
        self.article_details = {}
        
    def set_goal(self, category: str, complexity: str = "medium"):
        """Define qué artículo quiere crear el usuario simulado"""
        self.goal = f"Quiero crear un artículo de la categoría {category}."
        
        # Detalle interno que el agente "sabe" pero no necesariamente dice de inmediato
        if category == "EPP":
            self.article_details = {"producto": "Guantes", "material": "Nitrilo", "talla": "L", "uso": "Químico"}
        elif category == "WOG":
            self.article_details = {"producto": "Codo", "material": "PVC", "medida": "110mm", "angulo": "90 grados"}
        elif category == "ELECTRICIDAD":
            self.article_details = {"producto": "Cable", "tipo": "THHN", "calibre": "12AWG", "color": "Rojo"}
        else:
            self.article_details = {"producto": "Generico", "descripcion": "Articulo de prueba"}

        self.complexity = complexity

    def generate_response(self, chatbot_history: list) -> str:
        """Genera la respuesta del usuario basada en lo que dijo el chatbot"""
        
        system_prompt = f"""
        Estás simulando ser un usuario de un sistema de logística.
        Tu objetivo actual es: {self.goal}
        
        Tus datos reales (lo que tienes en tu mente) son: {self.article_details}
        
        PERFIL DE COMPORTAMIENTO: {self._get_profile_instruction()}
        
        Instrucciones:
        1. Responde a la última pregunta del chatbot.
        2. NO des toda la información de golpe a menos que seas el perfil 'Experto'.
        3. Mantén el rol. Sé breve si es necesario.
        4. Si el chatbot te confirma la creación del artículo, responde con "GRACIAS" o "CONFIRMO".
        """
        
        # Convertir historial simplificado para el prompt
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chatbot_history])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", f"Historial de conversación:\n{conversation_text}\n\nTu respuesta:")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({})

    def _get_profile_instruction(self) -> str:
        profiles = {
            "standard": "Eres un usuario cooperativo. Respondes lo que te preguntan de forma clara.",
            "confused": "No sabes mucho de términos técnicos. Usas sinónimos informales (ej: 'coso', 'cuestión'). A veces das la talla cuando te piden el color.",
            "impatient": "Eres directo y cortante. Das respuestas de una sola palabra. Te molesta que te pregunten mucho.",
            "expert": "Eres muy técnico. Das todos los detalles (SKU, norma, medidas precisas) en el primer mensaje.",
            "typo_king": "Cometes errores ortográficos intencionales y escribes las unidades mal (ej: '50ml' en vez de 'mm')."
        }
        return profiles.get(self.role_profile, profiles["standard"])
