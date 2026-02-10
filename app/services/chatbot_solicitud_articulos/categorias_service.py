"""
Servicio de categorías para artículos.
Centraliza la lógica de categorización e inferencia.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import lru_cache
from dataclasses import dataclass


@dataclass
class CategoriaInfo:
    """Información de una categoría de artículo."""
    id: str
    nombre: str
    descripcion: str
    keywords: List[str]
    formato: str
    campos: Dict[str, Any]


@dataclass
class InferenciaResultado:
    """Resultado de inferir una categoría."""
    categoria_inferida: Optional[str]
    descripcion: Optional[str]
    confianza: str  # ALTA, MEDIA, BAJA
    palabras_detectadas: List[str]
    alternativas: List[Dict[str, str]]


# Keywords por categoría (fuente única de verdad)
CATEGORIA_KEYWORDS: Dict[str, Dict[str, Any]] = {
    "EPP": {
        "nombre": "EPP",
        "descripcion": "Elementos de Protección Personal",
        "keywords": ["CASCO", "GUANTE", "ZAPATO", "BOTA", "BOTOTO", "LENTE", "ANTIPARRA", "ARNES", "RESPIRADOR", 
                    "MASCARILLA", "OVEROL", "CHALECO", "PARKA", "PANTALON", "CHAQUETA", "BUZO", "PROTECTOR AUDITIVO",
                    "TAPON OIDO", "OREJERA", "CARETA", "VISOR", "MEDIO ROSTRO", "CARA COMPLETA", "SEGURIDAD"]
    },
    "WOG": {
        "nombre": "WOG",
        "descripcion": "Water, Oil, Gas (Piping)",
        "keywords": ["CODO", "TEE", "VALVULA", "CAÑERIA", "FLANGE", "NIPPLE", "COPLA", "UNION AMERICANA",
                    "REDUCCION", "BUSHING", "TAPON", "FITTING", "NPT", "BSP", "ROSCADA", "SOLDADA", "BRIDADA",
                    "INOX 304", "INOX 316", "GALVANIZADO", "SCH40", "SCH80", "150#", "300#"]
    },
    "ELECTRICIDAD": {
        "nombre": "Electricidad",
        "descripcion": "Materiales Eléctricos",
        "keywords": ["CABLE", "AUTOMATICO", "DIFERENCIAL", "CONTACTOR", "ENCHUFE", "INTERRUPTOR", 
                    "TOMACORRIENTE", "CANALETA", "FOCO LED", "TUBO LED", "REFLECTOR", "GUARDAMOTOR",
                    "RELE TERMICO", "PRENSAESTOPA", "CINTA AISLADORA", "THHN", "CONCENTRICO", "EXTENSION ELECTRICA"]
    },
    "INSTRUMENTACION": {
        "nombre": "Instrumentación",
        "descripcion": "Instrumentos de Medición",
        "keywords": ["MANOMETRO", "TERMOMETRO", "FLUJOMETRO", "SENSOR", "TRANSMISOR", "DETECTOR",
                    "ANALIZADOR", "CONTROLADOR", "PRESOSTATO", "TERMOSTATO", "TESTER", "MULTIMETRO",
                    "MEDIDOR", "INDICADOR", "PSI", "BAR", "°C", "SCFM"]
    },
    "HERRAMIENTAS": {
        "nombre": "Herramientas",
        "descripcion": "Herramientas Manuales y Abrasivos",
        "keywords": ["LLAVE", "ALICATE", "DESTORNILLADOR", "MARTILLO", "COMBO", "CINCEL", "FLEXOMETRO",
                    "NIVEL", "ESCUADRA", "SIERRA", "ARCO SIERRA", "TARRAJA", "GATA", "STILSON", "FRANCESA",
                    "DISCO CORTE", "DISCO DESBASTE", "DISCO FLAP", "LIJA", "PIEDRA ESMERIL", "BROCHA", "RODILLO"]
    },
    "EQUIPOS": {
        "nombre": "Equipos",
        "descripcion": "Maquinaria y Equipos Mayores",
        "keywords": ["GENERADOR", "COMPRESOR", "SOLDADORA", "ESMERIL ANGULAR", "TALADRO", "ROTOMARTILLO",
                    "SIERRA CIRCULAR", "HIDROLAVADORA", "VIBRADOR", "BETONERA", "MOTOBOMBA", "TRONZADORA",
                    "MAKITA", "DEWALT", "BOSCH", "HONDA", "CATERPILLAR", "LINCOLN"]
    },
    "CONSTRUCCION": {
        "nombre": "Construcción",
        "descripcion": "Materiales de Construcción y Estructuras",
        "keywords": ["FIERRO", "CEMENTO", "ARENA", "GRAVILLA", "RIPIO", "TERCIADO", "OSB", "MADERA",
                    "PLANCHA", "PERFIL", "ANGULO", "CONSTANERA", "VIGA", "PLATINA", "BARRA", "MALLA ACMA",
                    "YESO", "CLAVO", "TORNILLO VOLCANITA", "ESTRUCTURA"]
    },
    "VEHICULOS": {
        "nombre": "Vehículos",
        "descripcion": "Repuestos Automotrices",
        "keywords": ["FILTRO ACEITE", "FILTRO COMBUSTIBLE", "FILTRO AIRE", "PASTILLA FRENO", "DISCO FRENO",
                    "AMORTIGUADOR", "CORREA", "BOMBA AGUA", "ALTERNADOR", "PARTIDA", "BATERIA", "NEUMATICO",
                    "HILUX", "L200", "NP300", "HINO", "VOLVO", "CAMIONETA", "CAMION"]
    },
    "COMPUTACIONAL": {
        "nombre": "Computacional",
        "descripcion": "Equipos y Accesorios TI",
        "keywords": ["NOTEBOOK", "LAPTOP", "PC", "COMPUTADOR", "MONITOR", "IMPRESORA", "MOUSE", "TECLADO",
                    "DISCO DURO", "MEMORIA RAM", "PENDRIVE", "SWITCH RED", "ROUTER", "TONER", "SCANNER",
                    "HP", "DELL", "LENOVO", "ASUS", "EPSON", "BROTHER"]
    },
    "FERRETERIA": {
        "nombre": "Ferretería",
        "descripcion": "Pernos, Tuercas, Fijaciones",
        "keywords": ["PERNO", "TUERCA", "GOLILLA", "VOLANDA", "CLAVO", "TORNILLO", "AUTORROSCANTE",
                    "PERNO ANCLAJE", "ESPARRAGO", "CHAVETA", "PRISIONERO", "REMACHE", "INSERTO", "PERNO EN U"]
    },
    "ASEO": {
        "nombre": "Aseo",
        "descripcion": "Productos de Limpieza",
        "keywords": ["CLORO", "DETERGENTE", "LAVALOZA", "DESENGRASANTE", "DESINFECTANTE", "JABON",
                    "PAPEL HIGIENICO", "TOALLA PAPEL", "BOLSA BASURA", "ESCOBA", "TRAPERO", "ESPONJA", "LYSOFORM"]
    },
    "OFICINA": {
        "nombre": "Oficina",
        "descripcion": "Artículos de Escritorio",
        "keywords": ["LAPIZ", "CUADERNO", "BLOCK", "CARPETA", "ARCHIVADOR", "CORCHETERA", "PERFORADORA",
                    "TIJERA", "CINTA ADHESIVA", "CLIPS", "CORCHETES", "RESMA PAPEL", "SOBRE", "PLUMON", "GOMA"]
    },
    "CONSUMIBLES": {
        "nombre": "Consumibles",
        "descripcion": "Consumo General, Cafetería, Embalaje",
        "keywords": ["PILAS", "BATERIAS", "BLOQUEADOR SOLAR", "BOTIQUIN", "CAFE", "AZUCAR", "TE", "NESCAFE",
                    "AGUA", "LECHE", "GALLETAS", "MILO", "STRETCH FILM", "CINTA EMBALAJE", "ZUNCHO", "VASO DESECHABLE"]
    },
    "SOLDADURA": {
        "nombre": "Soldadura",
        "descripcion": "Consumibles de Soldadura",
        "keywords": ["ELECTRODO", "ALAMBRE MIG", "VARILLA TIG", "APORTE TIG", "FUNDENTE", "FLUX",
                    "ANTORCHA", "TOBERA", "BOQUILLA", "PINZA MASA", "PORTA ELECTRODO", "CARETA SOLDAR", "VIDRIO SOLDAR",
                    "E6011", "E7018", "ER70S"]
    },
    "PINTURA": {
        "nombre": "Pintura",
        "descripcion": "Pinturas, Diluyentes y Accesorios",
        "keywords": ["ESMALTE", "LATEX", "ANTICORROSIVO", "PRIMER", "EPOXICO", "ZINCROMATO", "SPRAY",
                    "DILUYENTE", "THINNER", "AGUARRAS", "MASILLA", "CINTA MASKING", "PISTOLA PINTAR", "BANDEJA"]
    },
    "QUIMICOS": {
        "nombre": "Químicos",
        "descripcion": "Gases y Productos Químicos",
        "keywords": ["GAS ARGON", "GAS CO2", "GAS MEZCLA", "GAS OXIGENO", "GAS ACETILENO", "GAS PROPANO",
                    "CATALIZADOR", "RESINA", "ENDURECEDOR", "SELLADOR", "SILICONA", "ADHESIVO", "LUBRICANTE",
                    "REFRIGERANTE", "ANTICONGELANTE", "CILINDRO"]
    },
    "IZAJE": {
        "nombre": "Izaje",
        "descripcion": "Elementos de Izaje y Amarre",
        "keywords": ["ESLINGA", "ESTROBO", "GRILLETE", "GANCHO", "CADENA", "TENSOR", "TECLE",
                    "CARRO PORTACADENA", "CABO DE VIDA", "LINEA DE VIDA", "TON", "TONELADA"]
    },
    "SEGURIDAD_INDUSTRIAL": {
        "nombre": "Seguridad Industrial",
        "descripcion": "Señalética, Bloqueos y Emergencia",
        "keywords": ["SEÑALETICA", "LETRERO", "CONO", "BARRERA", "CINTA DEMARCATORIA", "CINTA PELIGRO",
                    "CANDADO BLOQUEO", "PINZA BLOQUEO", "TARJETA BLOQUEO", "EXTINTOR", "MANTA IGNIFUGA",
                    "DUCHA LAVAOJOS", "ALCOTEST"]
    },
    "COMBUSTIBLE": {
        "nombre": "Combustible",
        "descripcion": "Combustibles y Lubricantes",
        "keywords": ["PETROLEO", "DIESEL", "BENCINA", "GASOLINA", "ACEITE MOTOR", "ACEITE HIDRAULICO",
                    "ACEITE TRANSMISION", "GRASA", "15W40", "10W40", "5W30", "80W90", "ISO 32", "ISO 46", "EP2"]
    }
}


@lru_cache(maxsize=1)
def cargar_config() -> Dict[str, Any]:
    """Carga la configuración del YAML con cache."""
    config_path = Path("config/estandarizacion_articulos.yaml")
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def obtener_categorias() -> List[Dict[str, str]]:
    """Retorna lista de categorías disponibles."""
    return [
        {"id": cat_id, "nombre": data["nombre"], "descripcion": data["descripcion"]}
        for cat_id, data in CATEGORIA_KEYWORDS.items()
    ]


def obtener_reglas_categoria(categoria: str) -> Optional[Dict[str, Any]]:
    """Obtiene las reglas de configuración para una categoría."""
    config = cargar_config()
    return config.get(categoria)


def inferir_categoria(descripcion: str) -> InferenciaResultado:
    """
    Analiza la descripción de un artículo e infiere la categoría más probable.
    
    Args:
        descripcion: Texto libre describiendo el artículo
    
    Returns:
        InferenciaResultado con la categoría inferida y confianza
    """
    texto = descripcion.upper()
    
    # Calcular puntuación por categoría
    scores: Dict[str, Dict[str, Any]] = {}
    
    for cat_id, data in CATEGORIA_KEYWORDS.items():
        score = 0
        matches = []
        for keyword in data["keywords"]:
            if keyword in texto:
                score += len(keyword)  # Palabras más largas = más puntos
                matches.append(keyword)
        if score > 0:
            scores[cat_id] = {
                "score": score, 
                "matches": matches, 
                "descripcion": data["descripcion"]
            }
    
    # Sin coincidencias
    if not scores:
        return InferenciaResultado(
            categoria_inferida=None,
            descripcion=None,
            confianza="BAJA",
            palabras_detectadas=[],
            alternativas=[]
        )
    
    # Ordenar por puntuación
    sorted_cats = sorted(scores.items(), key=lambda x: -x[1]["score"])
    top = sorted_cats[0]
    
    # Determinar confianza
    confianza = "ALTA" if top[1]["score"] > 15 else "MEDIA" if top[1]["score"] > 8 else "BAJA"
    
    # Alternativas (máximo 2)
    alternativas = [
        {"categoria": c, "descripcion": d["descripcion"]} 
        for c, d in sorted_cats[1:3]
    ]
    
    return InferenciaResultado(
        categoria_inferida=top[0],
        descripcion=top[1]["descripcion"],
        confianza=confianza,
        palabras_detectadas=top[1]["matches"],
        alternativas=alternativas
    )
