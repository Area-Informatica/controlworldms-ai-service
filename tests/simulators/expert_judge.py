"""
LLM-as-a-Judge Module
=====================
Juez experto por categoría que evalúa si el artículo estandarizado es válido,
coherente y representa un producto real/existente en la industria.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import yaml
import os


class JudgmentResult(BaseModel):
    """Esquema estructurado del veredicto del juez."""
    valido: bool = Field(description="True si el artículo estandarizado es válido y coherente")
    puntuacion: int = Field(description="Puntuación de 1 a 10 (10 = perfecto)")
    existe_en_industria: bool = Field(description="True si el producto descrito existe realmente en la industria")
    formato_correcto: bool = Field(description="True si sigue el formato esperado de la categoría")
    campos_coherentes: bool = Field(description="True si los campos combinados tienen sentido técnico")
    razonamiento: str = Field(description="Explicación del juicio en 2-3 oraciones")
    sugerencia: Optional[str] = Field(default=None, description="Sugerencia de mejora si aplica")


class ExpertJudgeAgent:
    """
    Juez LLM experto por categoría que evalúa la calidad de la estandarización.
    
    Cada categoría tiene un prompt especializado con conocimiento de dominio
    para evaluar si el artículo resultante es válido y representa un 
    producto real de la industria.
    """
    
    def __init__(self, model: str = "claude-3-haiku-20240307"):
        """
        Args:
            model: Modelo de Anthropic a usar. Por defecto usamos Haiku que es rápido y suele estar disponible.
                   Para juicios más profundos usar 'claude-3-opus-20240229' o 'claude-3-5-sonnet-20240620'.
        """
        self.llm = ChatAnthropic(model=model, temperature=0)
        self.parser = JsonOutputParser(pydantic_object=JudgmentResult)
        self._category_config = self._load_category_config()
        
    def _load_category_config(self) -> dict:
        """Carga la configuración de categorías desde el YAML."""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'config', 'estandarizacion_articulos.yaml'
        )
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
    
    def judge(
        self, 
        category: str, 
        standardized_name: str, 
        original_input: dict,
        conversation_history: str = ""
    ) -> JudgmentResult:
        """
        Evalúa si el artículo estandarizado es válido.
        
        Args:
            category: Categoría del artículo (EPP, WOG, ELECTRICIDAD, etc.)
            standardized_name: Nombre final estandarizado (ej: "OVEROL CABRITILLA (44)")
            original_input: Datos originales proporcionados por el usuario simulado
            conversation_history: Historial de la conversación (opcional)
            
        Returns:
            JudgmentResult con el veredicto estructurado
        """
        system_prompt = self._get_expert_system_prompt(category)
        format_info = self._get_format_info(category)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
EVALUACIÓN SOLICITADA:
======================

**Categoría:** {category}
**Formato esperado:** {format_info}

**Datos originales del usuario:**
{original_input}

**Nombre estandarizado resultante:**
"{standardized_name}"

**Historial de conversación (si aplica):**
{conversation_history}

Por favor, evalúa este resultado y proporciona tu veredicto como JSON.

{format_instructions}
""")
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            result = chain.invoke({
                "category": category,
                "format_info": format_info,
                "original_input": str(original_input),
                "standardized_name": standardized_name,
                "conversation_history": conversation_history or "N/A",
                "format_instructions": self.parser.get_format_instructions()
            })
            return JudgmentResult(**result)
        except Exception as e:
            # Fallback en caso de error de parsing
            return JudgmentResult(
                valido=False,
                puntuacion=0,
                existe_en_industria=False,
                formato_correcto=False,
                campos_coherentes=False,
                razonamiento=f"Error al evaluar: {str(e)}",
                sugerencia="Revisar el formato de salida del juez."
            )
    
    def _get_format_info(self, category: str) -> str:
        """Obtiene el formato esperado de la categoría desde el YAML."""
        if category in self._category_config:
            cat_config = self._category_config[category]
            formato = cat_config.get('formato', 'No definido')
            campos = cat_config.get('campos', {})
            campos_str = ", ".join([
                f"{k} ({'requerido' if v.get('requerido') else 'opcional'})" 
                for k, v in campos.items()
            ])
            return f"Formato: {formato}\nCampos: {campos_str}"
        return "Formato no definido en configuración"
    
    def _get_expert_system_prompt(self, category: str) -> str:
        """
        Retorna el prompt de sistema especializado para cada categoría.
        Cada prompt contiene conocimiento de dominio específico.
        """
        
        base_instructions = """
Eres un JUEZ EXPERTO evaluando la calidad de artículos estandarizados en un sistema de logística industrial.

Tu rol es determinar si el nombre estandarizado:
1. Representa un producto REAL que existe en la industria
2. Tiene coherencia técnica (los campos combinados tienen sentido)
3. Sigue el formato esperado de la categoría
4. Contiene información suficiente para identificar/comprar el producto

IMPORTANTE:
- Sé estricto pero justo
- Un producto puede ser válido aunque no sea común
- Evalúa la coherencia técnica, no solo la existencia del nombre
- Considera variantes regionales de nombres de productos
"""

        category_expertise = {
            "EPP": """
ESPECIALIDAD: Elementos de Protección Personal

CONOCIMIENTO DE DOMINIO:
- Subtipos válidos: cascos, lentes, guantes, botas, arneses, respiradores, overoles, etc.
- Materiales comunes: nitrilo, latex, cabritilla, kevlar, neopreno, PVC
- Tallas: XS-XXL para ropa, números 36-45 para calzado, "UNICA" para cascos/lentes
- Certificaciones relevantes: ANSI, EN, NFPA (pero no requeridas en el nombre)

CRITERIOS ESPECÍFICOS:
- Un "GUANTE NITRILO L" es válido
- Un "CASCO SOLDADOR CABRITILLA" NO es válido (mezcla incorrecta de atributos)
- "OVEROL CABRITILLA (44)" es válido si existe ropa de trabajo de cabritilla talla 44
- Evaluar si la combinación subtipo+material tiene sentido industrial
""",

            "WOG": """
ESPECIALIDAD: Water, Oil, Gas (Fitting y Válvulas)

CONOCIMIENTO DE DOMINIO:
- Subtipos: codos, tees, reducciones, válvulas, flanges, cañerías, mangueras
- Materiales: INOX 304/316, acero carbono, galvanizado, bronce, PVC, CPVC, HDPE
- Diámetros estándar: 1/4", 1/2", 3/4", 1", 2", 3", 4", 6" (pulgadas)
- Conexiones: NPT, BSP, soldada (SW/BW), bridada, ranurada
- Ratings: 150#, 300#, 600#, 3000#, SCH40, SCH80

CRITERIOS ESPECÍFICOS:
- "CODO 90 1/2" INOX 304 ROSCADA NPT" es válido y completo
- "VALVULA PVC 2 PULGADAS" es válido pero le falta conexión
- El diámetro DEBE coincidir en todo el ensamble
- Verificar que el material sea compatible con el tipo de conexión
""",

            "ELECTRICIDAD": """
ESPECIALIDAD: Materiales Eléctricos

CONOCIMIENTO DE DOMINIO:
- Cables: THHN, concentrico, soldador. Calibres: AWG o mm² (2.5, 4, 6, 10 mm²)
- Protecciones: automáticos, diferenciales, guardamotores. Amperajes: 10A, 16A, 25A, 32A
- Accesorios: enchufes, tomacorrientes, canaletas, prensaestopas
- Iluminación: focos/tubos LED, reflectores, con potencias en W

CRITERIOS ESPECÍFICOS:
- "CABLE THHN 2.5MM2" o "CABLE THHN 12AWG" son válidos
- "AUTOMATICO 25A" es válido
- "FOCO LED 100W" es válido
- La especificación debe incluir valores eléctricos relevantes (calibre, amperaje, potencia)
""",

            "ASEO": """
ESPECIALIDAD: Productos de Limpieza e Higiene

CONOCIMIENTO DE DOMINIO:
- Productos: cloro, detergente, desengrasante, desinfectante, jabón, papel higiénico
- Formatos/presentaciones: 1L, 5L, 20L, bidón, rollo, paquete, spray

CRITERIOS ESPECÍFICOS:
- "CLORO 5L" es válido
- "DETERGENTE PAQUETE" es válido pero el formato podría ser más específico
- Debe tener producto + presentación/formato
""",

            "COMBUSTIBLE": """
ESPECIALIDAD: Combustibles y Lubricantes

CONOCIMIENTO DE DOMINIO:
- Tipos: diésel, bencina, aceites motor/hidráulico/transmisión, grasa
- Grados: octanaje (93, 95, 97), viscosidades (15W40, 5W30, 80W90), ISO
- Formatos: litro, galón, balde 19L, tambor 208L, IBC 1000L

CRITERIOS ESPECÍFICOS:
- "ACEITE MOTOR 15W40 BALDE 19L" es válido y completo
- "PETROLEO DIESEL LITRO" es válido
- El grado debe ser apropiado para el tipo de producto
""",

            "CONSTRUCCION": """
ESPECIALIDAD: Materiales de Construcción y Estructuras

CONOCIMIENTO DE DOMINIO:
- Materiales: fierro estriado, perfiles, planchas, cemento, madera, OSB, yeso cartón
- Dimensiones: diámetros (8mm, 12mm), medidas (50x50x3mm), largos (6m)

CRITERIOS ESPECÍFICOS:
- "FIERRO ESTRIADO 8MM" es válido
- "PERFIL CUADRADO 50X50X3MM 6M" es válido
- Las dimensiones deben ser realistas y en formato industrial
""",

            "VEHICULOS": """
ESPECIALIDAD: Repuestos Automotrices

CONOCIMIENTO DE DOMINIO:
- Vehículos: Hilux, L200, NP300, Hino, Volvo FH (modelo O identificador)
- Repuestos: filtros, pastillas, discos, amortiguadores, baterías, neumáticos

CRITERIOS ESPECÍFICOS:
- "HILUX 2.4 FILTRO ACEITE" es válido
- El nombre del vehículo debe preceder al repuesto
- Opcionalmente puede incluir año o motorización
""",

            "INSTRUMENTACION": """
ESPECIALIDAD: Instrumentos de Medición y Control

CONOCIMIENTO DE DOMINIO:
- Tipos: manómetros, termómetros, flujómetros, sensores, transmisores
- Variables: presión, temperatura, flujo, nivel, pH, gases
- Rangos: 0-10 BAR, 0-100 PSI, 0-200°C

CRITERIOS ESPECÍFICOS:
- "MANOMETRO PRESION 0-10 BAR" es válido
- "SENSOR TEMPERATURA" es válido pero le falta rango
- Debe indicar qué variable mide
""",

            "EQUIPOS": """
ESPECIALIDAD: Maquinaria y Equipos Mayores

CONOCIMIENTO DE DOMINIO:
- Tipos: generadores, compresores, soldadoras, taladros, esmeriladoras
- Marcas: Honda, Caterpillar, Lincoln, Makita, DeWalt, Bosch
- Capacidades: 5KVA, 100L, 250A, 7 pulgadas, HP

CRITERIOS ESPECÍFICOS:
- "GENERADOR HONDA 5KVA" es válido
- "ESMERIL ANGULAR MAKITA 7 PULGADAS" es válido
- La marca es importante en esta categoría
""",

            "HERRAMIENTAS": """
ESPECIALIDAD: Herramientas Manuales y Abrasivos

CONOCIMIENTO DE DOMINIO:
- Herramientas: alicates, destornilladores, llaves, martillos, flexómetros
- Abrasivos: discos corte/desbaste/flap, lijas, piedras esmeril
- Medidas: pulgadas, milímetros, sets

CRITERIOS ESPECÍFICOS:
- "LLAVE PUNTA CORONA 1/2" es válido
- "DISCO CORTE 4-1/2X1/16X7/8" es válido (formato estándar)
- "FLEXOMETRO 5M" es válido
""",

            "COMPUTACIONAL": """
ESPECIALIDAD: Equipos y Accesorios de Computación

CONOCIMIENTO DE DOMINIO:
- Productos: notebooks, monitores, impresoras, periféricos, redes
- Specs: I5 8GB 256SSD, pulgadas, puertos, capacidades
- Marcas: HP, Dell, Lenovo, Logitech, Samsung

CRITERIOS ESPECÍFICOS:
- "NOTEBOOK HP I5 8GB 256SSD" es válido
- "MONITOR 24 PULGADAS" es válido
- Las especificaciones deben ser realistas
""",

            "SOLDADURA": """
ESPECIALIDAD: Equipos y Consumibles de Soldadura

CONOCIMIENTO DE DOMINIO:
- Consumibles: electrodos, alambre MIG, varilla TIG
- Especificaciones: E6011 3.2MM, ER70S-6 1.0MM, INOX 316L
- Accesorios: antorchas, toberas, reguladores

CRITERIOS ESPECÍFICOS:
- "ELECTRODO E6011 3.2MM" es válido (código AWS estándar)
- "ALAMBRE MIG ER70S-6 1.0MM" es válido
- Los códigos de soldadura deben existir (E6011, E7018, ER70S-6, etc.)
""",

            "PINTURA": """
ESPECIALIDAD: Pinturas, Diluyentes y Accesorios

CONOCIMIENTO DE DOMINIO:
- Productos: esmalte sintético, látex, anticorrosivo, primer, epóxico
- Colores: blanco, negro, gris, rojo, amarillo, azul, verde
- Formatos: 1/4GL, 1GL, 5GL, 1L, spray 400ml

CRITERIOS ESPECÍFICOS:
- "ESMALTE SINTETICO BLANCO 1GL" es válido y completo
- "ANTICORROSIVO ROJO 1GL" es válido
- Los diluyentes y accesorios no llevan color
""",

            "SEGURIDAD_INDUSTRIAL": """
ESPECIALIDAD: Señalética, Bloqueos y Emergencia

CONOCIMIENTO DE DOMINIO:
- Señalética: señales, letreros, conos, barreras, cintas
- Bloqueo: candados, pinzas, tarjetas LOTO
- Emergencia: extintores, mantas ignífugas, duchas lavaojos

CRITERIOS ESPECÍFICOS:
- "EXTINTOR 6KG ABC" es válido
- "CANDADO BLOQUEO ROJO" es válido
- "SEÑALETICA USO EPP OBLIGATORIO" es válido
""",

            "FERRETERIA": """
ESPECIALIDAD: Pernos, Tuercas, Golillas, Fijaciones

CONOCIMIENTO DE DOMINIO:
- Tipos: pernos, tuercas, golillas, tornillos, clavos, remaches
- Medidas: pulgadas (1/4x1, 3/8x2) o métricas (M8x25, M10x40)
- Materiales: acero, inox, galvanizado, bronce

CRITERIOS ESPECÍFICOS:
- "PERNO 1/4X1 INOX" es válido
- "TUERCA M10 GALVANIZADO" es válido
- La medida debe ser coherente (diámetro x largo o solo métrica)
""",

            "QUIMICOS": """
ESPECIALIDAD: Gases, Catalizadores, Selladores, Adhesivos

CONOCIMIENTO DE DOMINIO:
- Gases: argón, CO2, oxígeno, acetileno, propano
- Adhesivos: siliconas, selladores, resinas, catalizadores
- Presentaciones: cilindro, cartucho, litros, kg

CRITERIOS ESPECÍFICOS:
- "GAS ARGON CILINDRO 10M3" es válido
- "SILICONA CARTUCHO 300ML" es válido
- La presentación debe ser apropiada al producto
""",

            "CONSUMIBLES": """
ESPECIALIDAD: Consumo General, Cafetería, Embalaje

CONOCIMIENTO DE DOMINIO:
- General: pilas, baterías, bloqueador solar, botiquín
- Cafetería: café, azúcar, té, agua
- Embalaje: stretch film, cinta embalaje, zuncho

CRITERIOS ESPECÍFICOS:
- "CAFE 1KG" es válido
- "STRETCH FILM 50CM" es válido
- "PILAS AA PACK 4" es válido
""",

            "IZAJE": """
ESPECIALIDAD: Elementos de Izaje y Amarre

CONOCIMIENTO DE DOMINIO:
- Elementos: eslingas (planas/redondas), estrobos, grilletes, tecles
- Capacidades: TON (1TON, 2TON, 5TON), pulgadas para grilletes
- Largos: metros (3M, 6M, 10M)

CRITERIOS ESPECÍFICOS:
- "ESLINGA PLANA 2TON 3M" es válido y completo
- "GRILLETE 3/4" es válido (el diámetro implica capacidad)
- La capacidad de carga es CRÍTICA en esta categoría por seguridad
"""
        }
        
        # Obtener expertise específica o usar genérica
        expertise = category_expertise.get(category, f"""
ESPECIALIDAD: {category}

No tengo conocimiento específico detallado de esta categoría, pero evaluaré:
- Si el nombre parece representar un producto real
- Si sigue una estructura lógica tipo+especificación
- Si los valores tienen coherencia industrial general
""")
        
        return base_instructions + "\n\n" + expertise


def format_judgment_report(result: JudgmentResult, category: str, standardized_name: str) -> str:
    """Formatea el resultado del juicio para mostrarlo en consola."""
    emoji_valid = "✅" if result.valido else "❌"
    emoji_exists = "✓" if result.existe_en_industria else "✗"
    emoji_format = "✓" if result.formato_correcto else "✗"
    emoji_coherent = "✓" if result.campos_coherentes else "✗"
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║  VEREDICTO DEL JUEZ EXPERTO ({category})
╠══════════════════════════════════════════════════════════════╣
║  Artículo evaluado: "{standardized_name}"
║  
║  {emoji_valid} RESULTADO: {"VÁLIDO" if result.valido else "NO VÁLIDO"}
║  📊 Puntuación: {result.puntuacion}/10
║  
║  Checklist:
║    [{emoji_exists}] Existe en la industria
║    [{emoji_format}] Formato correcto
║    [{emoji_coherent}] Campos coherentes
║  
║  💬 Razonamiento:
║     {result.razonamiento}
"""
    if result.sugerencia:
        report += f"""║  
║  💡 Sugerencia: {result.sugerencia}
"""
    report += "╚══════════════════════════════════════════════════════════════╝"
    
    return report


# Ejemplo de uso standalone
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    judge = ExpertJudgeAgent()
    
    # Test EPP
    result = judge.judge(
        category="EPP",
        standardized_name="OVEROL CABRITILLA (44)",
        original_input={"subtipo": "OVEROL", "descripcion": "CABRITILLA", "talla": 44}
    )
    print(format_judgment_report(result, "EPP", "OVEROL CABRITILLA (44)"))
    
    # Test WOG
    result = judge.judge(
        category="WOG",
        standardized_name="CODO 90 1/2\" INOX 304 ROSCADA NPT",
        original_input={"subtipo": "CODO", "diametro": "1/2\"", "material": "INOX 304", "conexion": "ROSCADA NPT"}
    )
    print(format_judgment_report(result, "WOG", "CODO 90 1/2\" INOX 304 ROSCADA NPT"))
