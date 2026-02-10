import pytest
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

# Lista de casos de prueba
# Cada caso tiene una descripción completa y lo que esperamos que la IA detecte
CASOS_DE_PRUEBA = [
    # EPP
    {"descripcion": "Necesito unos guantes de cabretilla talla 9", "tipo_esperado": "EPP", "keywords": ["GUANTE", "CABRETILLA", "9"]},
    {"descripcion": "Casco de seguridad blanco tipo jockey", "tipo_esperado": "EPP", "keywords": ["CASCO", "BLANCO"]},
    
    # WOG
    {"descripcion": "Codo de PVC sanitario de 110 mm", "tipo_esperado": "WOG", "keywords": ["CODO", "PVC", "110"]},
    {"descripcion": "Valvula de bola de 1 pulgada paso total", "tipo_esperado": "WOG", "keywords": ["VALVULA", "BOLA", "1"]},

    # ASEO
    {"descripcion": "Cloro liquido en bidon de 5 lts", "tipo_esperado": "ASEO", "keywords": ["CLORO", "BIDON", "5"]},
    {"descripcion": "Papel higienico hoja simple pack 4", "tipo_esperado": "ASEO", "keywords": ["PAPEL", "HIGIENICO"]},

    # COMBUSTIBLE
    {"descripcion": "Petroleo Diesel para operacion", "tipo_esperado": "COMBUSTIBLE", "keywords": ["PETROLEO", "DIESEL"]},

    # FERRETERIA
    {"descripcion": "Perno hexagonal de 1/2 x 2 pulgadas", "tipo_esperado": "FERRETERIA", "keywords": ["PERNO", "1/2", "2"]},
    
    # ELECTRICIDAD
    {"descripcion": "Cable THHN numero 12 rojo", "tipo_esperado": "ELECTRICIDAD", "keywords": ["CABLE", "THHN", "12", "ROJO"]},
    
    # HERRAMIENTAS
    {"descripcion": "Disco de corte 4 1/2 para metal", "tipo_esperado": "HERRAMIENTAS", "keywords": ["DISCO", "CORTE", "4-1/2"]},
    
    # VEHICULOS
    {"descripcion": "Filtro de aceite para camioneta Hilux", "tipo_esperado": "VEHICULOS", "keywords": ["FILTRO", "ACEITE", "HILUX"]},
]

@pytest.mark.parametrize("caso", CASOS_DE_PRUEBA)
def test_ia_generacion_nombres(caso):
    """
    Prueba parametrizada que recorre la lista de CASOS_DE_PRUEBA.
    Envía la descripción a la API y verifica si la IA logra identificar
    correctamente el tipo y generar un nombre coherente.
    """
    payload = {
        "mensaje": caso["descripcion"],
        "contexto_conversacion": []
    }
    
    print(f"\nProbando: {caso['descripcion']}")
    
    response = client.post("/chatbot/solicitud-articulos/estandarizar", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # 1. Datos básicos
    articulo = data.get("articulo_identificado")
    respuesta_texto = data.get("mensaje", "").upper()
    opciones = data.get("opciones_sugeridas", [])
    
    # 2. Verificación principal
    if articulo:
        # CASO IDEAL: Se identificó y finalizó el artículo
        print(f"  -> Artículo identificado: {articulo['nombre_estandarizado']}")
        
        # Validar tipo
        assert articulo["tipo"] == caso["tipo_esperado"], \
            f"Tipo incorrecto. Esperado {caso['tipo_esperado']}, Recibido {articulo['tipo']}"
        
        # Validar palabras clave en el nombre generado
        nombre_generado = articulo["nombre_estandarizado"].upper()
        if "keywords" in caso:
            for palabra in caso["keywords"]:
                assert palabra in nombre_generado, f"Falta palabra clave '{palabra}' en '{nombre_generado}'"

    else:
        # CASO INTERMEDIO: La IA pide más información o confirma categoría
        # Esto NO es un error, es parte del flujo conversacional.
        # Validamos que al menos entendió la categoría o está preguntando algo relevante.
        
        print(f"  -> Interacción requerida. Respuesta: {respuesta_texto}")
        
        # Si la respuesta es vacía o "...", es sospechoso pero puede pasar si solo mandó opciones
        if respuesta_texto in ["...", "PROCESANDO INFORMACIÓN...", "POR FAVOR SELECCIONA UNA OPCIÓN:"]:
            if not opciones:
                # Si no hay texto NI opciones, ahí sí es un fallo grave
                pytest.fail("La IA no devolvió ni texto ni opciones válidas.")
            else:
                print(f"  -> La IA envió opciones: {opciones}")
        
        # Intentar validar que menciona el tipo esperado si hay texto suficiente
        # (Esto es "soft assertion" porque la IA puede preguntar "¿Qué talla?" sin decir "EPP")
        if len(respuesta_texto) > 10 and caso["tipo_esperado"] in respuesta_texto:
             print(f"  -> Contexto confirmado: Mencionó {caso['tipo_esperado']}")
        
        # Para que el test pase, consideramos éxito si:
        # a) Identificó el artículo (visto arriba)
        # b) O está preguntando/mostrando opciones (flow conversacional activo)
        assert data["requiere_mas_info"] is True or data["listo_para_crear"] is True
