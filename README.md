# ControlWorldMS AI Service

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/LangChain-Latest-orange?logo=chainlink&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/Claude-Anthropic-blueviolet" alt="Anthropic">
</p>

## 📋 Descripción

**ControlWorldMS AI Service** es un microservicio de inteligencia artificial diseñado para extender las capacidades del sistema principal [ControlWorldMS](https://github.com/Area-Informatica/controlworldms). Proporciona endpoints de API REST que utilizan modelos de lenguaje avanzados (LLMs) para automatizar análisis complejos y tareas que requieren procesamiento de lenguaje natural.

### 🎯 Propósito Principal

Este microservicio actúa como el **cerebro de IA** del ecosistema ControlWorldMS, permitiendo:

- Análisis automatizado de incidentes de seguridad (HSE)
- Generación de reportes estructurados mediante IA
- Procesamiento de lenguaje natural para casos de uso específicos del negocio
- **Estandarización de Artículos (WIP):** Chatbot inteligente para la creación normalizada de materiales en el ERP Defontana.
- Escalabilidad independiente de las capacidades de IA

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                      ControlWorldMS (Laravel)                    │
│                         Puerto: 80/443                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP Request
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              ControlWorldMS AI Service (FastAPI)                 │
│                         Puerto: 8000                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Routers   │  │   Agents    │  │   Services  │              │
│  │  (hse.py)   │──│ (hse_agent) │──│ (llm_utils) │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Schemas   │  │   Prompts   │  │  LangChain  │              │
│  │  (Pydantic) │  │ (Templates) │  │  Anthropic  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Anthropic Claude    │
              │   (API Externa)       │
              └───────────────────────┘
```

---

## 📁 Estructura del Proyecto

```
controlworldms-ai-service/
├── main.py                     # Punto de entrada de la aplicación FastAPI
├── requirements.txt            # Dependencias del proyecto
├── .env.example               # Plantilla de variables de entorno
├── docs/                      # Documentación adicional
└── app/
    ├── __init__.py
    ├── agents/                # Agentes de IA (LangChain)
    │   └── hse_agent.py       # Agente especializado en HSE
    ├── prompts/               # Plantillas de prompts del sistema
    │   └── hse_prompts.py     # Prompts para análisis HSE
    ├── routers/               # Endpoints de la API
    │   └── hse.py             # Rutas del módulo HSE
    ├── schemas/               # Modelos de datos (Pydantic)
    │   └── hse_schemas.py     # Esquemas de request/response
    └── services/              # Servicios auxiliares
        └── llm_utils.py       # Utilidades para modelos LLM
```

---

## 🚀 Módulos Disponibles

### 1. Módulo Chatbot Solicitud de Artículos (Estandarización)

Sistema conversacional inteligente diseñado para ayudar a usuarios a crear artículos en el ERP respetando estándares técnicos estrictos.

- **Funcionalidades:**
    - Conversación dinámica para recolectar atributos técnicos.
    - Validación de datos en tiempo real (ej: Tallas, Normas de seguridad).
    - Generación automática de SKUs y Nombres Estandarizados.
    - Soporte multi-categoría (EPP, Ropa Corporativa, Herramientas, etc.).

### 2. Módulo HSE (Salud, Seguridad y Medio Ambiente)

#### Endpoint: `POST /hse/5-porques`

Realiza un análisis de **Causa Raíz** utilizando la metodología de los **5 Porqués** para incidentes de seguridad.

**Request:**

```json
{
  "correlativo": "INC-2024-001",
  "tipo_evento": "Accidente",
  "descripcion": "Trabajador sufrió caída desde escalera de 2 metros de altura",
  "accion_inmediata": "Traslado a centro médico",
  "area_proceso": "Producción",
  "origen": "Interno",
  "impacto": "Lesión moderada"
}
```

**Response:**

```json
{
  "analisis_5_porque": "1. ¿Por qué cayó el trabajador? Porque perdió el equilibrio...\n2. ¿Por qué perdió el equilibrio? Porque el peldaño estaba dañado...\n3. ¿Por qué estaba dañado? Porque no había un programa de inspección...\n4. ¿Por qué no había inspección? Porque no existe un procedimiento documentado...\n5. ¿Por qué no existe el procedimiento? Porque no se ha implementado un sistema de gestión de mantenimiento preventivo.",
  "causa_raiz": "Ausencia de un sistema de gestión de mantenimiento preventivo para equipos de trabajo en altura."
}
```

---

## ⚙️ Instalación

### Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)
- Cuenta de Anthropic con API Key

### Pasos de Instalación

1. **Clonar el repositorio:**

```bash
git clone https://github.com/Area-Informatica/controlworldms-ai-service.git
cd controlworldms-ai-service
```

2. **Crear entorno virtual:**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

3. **Instalar dependencias:**

```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
# Configuración del servidor
PORT=8000
APP_ENV=local

# Dominios permitidos (producción)
ALLOWED_ORIGINS=https://tu-dominio.cl

# API Key de Anthropic (REQUERIDO)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

5. **Ejecutar el servidor:**

```bash
# Desarrollo
uvicorn main:app --reload --port 8000

# Producción
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---


## 🧪 Testing y Simulación

El proyecto incluye un robusto sistema de **Simulación Multi-Agente (MAS)** para validar el desempeño del Chatbot sin intervención humana. Este framework permite ejecutar cientos de conversaciones simuladas para medir la tasa de éxito, la calidad de la estandarización y optimizar costos.

### Arquitectura de Pruebas

El sistema orquesta una interacción autónoma entre tres componentes principales:

1.  **Chatbot (SUT - System Under Test):** El agente real de IA (Claude-3.5-Sonnet) que intenta estandarizar el artículo.
2.  **User Simulator:** Un agente ligero (Claude-3-Haiku) que simula comportamientos humanos (ej: usuario confundido, experto, impaciente) y mantiene el estado de su objetivo (ej: "Quiero zapatos talla 42").
3.  **Expert Judge (LLM-as-a-Judge):** Un evaluador final (Claude-3-Haiku) que analiza el resultado (JSON del artículo creado) contra reglas estrictas de negocio, asignando un puntaje (1-10) y validando coherencia técnica.

### Optimización de Costos

Para minimizar el consumo de tokens en pruebas masivas:
-   **Regex & Heurísticas:** Se eliminaron evaluaciones LLM intermedias. El éxito de la simulación y la extracción del nombre estandarizado se realizan mediante Patrones Regulares optimizados.
-   **Failsafes:** Detectores de bucles infinitos (ej: bucles de agradecimiento) que cortan la simulación automáticamente.
-   **API Retry:** Implementación de *Exponential Backoff* para manejar errores de sobrecarga (529) de la API de Anthropic.

### Ejecución de Simulaciones (CLI)

El script `tests/test_multi_agent_simulation.py` soporta argumentos de línea de comandos para ejecuciones dinámicas:

```bash
# Uso básico: 3 iteraciones de EPP con usuario "confundido"
python tests/test_multi_agent_simulation.py -c EPP -p confused -n 3

# Ayuda completa
python tests/test_multi_agent_simulation.py --help
```

**Argumentos Disponibles:**

| Argumento | Flag | Opciones | Descripción |
|-----------|------|----------|-------------|
| Categoría | `-c` | `EPP`, `ROPA`, `HERRAMIENTAS`, `WOG`... | Categoría del artículo a simular. |
| Personalidad | `-p` | `standard`, `confused`, `expert`, `impatient` | Perfil del usuario simulado. |
| Iteraciones | `-n` | `1` a `100` | Número de simulaciones a ejecutar secuencialmente. |
| Debug | `--debug` | (flag) | Muestra logs detallados de cada mensaje en consola. |

### Métricas de Evaluación (Expert Judge)

Cada simulación exitosa es auditada por el Juez Experto bajo los siguientes criterios:
1.  **Validez:** ¿El artículo es un producto real?
2.  **Formato:** ¿Cumple la estructura `[NOUN] [ATTR1] [ATTR2]...`?
3.  **Coherencia:** ¿Tienen sentido los atributos combinados? (ej: No permitir "Zapatos dieléctricos de metal").

El reporte final incluye tasa de éxito (SR), puntaje promedio del juez y desglose de costos estimados.

## 🔌 Integración con ControlWorldMS (Laravel)

### Configuración en Laravel

1. Agregar variables de entorno en `.env`:

```env
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_TIMEOUT=60
```

2. Configurar en `config/services.php`:

```php
'ai_service' => [
    'base_url' => env('AI_SERVICE_URL', 'http://localhost:8000'),
    'timeout' => env('AI_SERVICE_TIMEOUT', 30),
],
```

3. Ejemplo de uso desde PHP:

```php
use Illuminate\Support\Facades\Http;

$response = Http::timeout(60)->post(config('services.ai_service.base_url') . '/hse/5-porques', [
    'tipo_evento' => 'Accidente',
    'descripcion' => 'Descripción del incidente...',
    'accion_inmediata' => 'Acción tomada',
    'area_proceso' => 'Producción',
    'origen' => 'Interno',
    'impacto' => 'Alto',
]);

$analysis = $response->json();
// $analysis['analisis_5_porque']
// $analysis['causa_raiz']
```

---

## 📚 API Reference

### Health Check

```http
GET /
```

**Response:**

```json
{
  "status": "online",
  "service": "ControlWorldMS AI",
  "version": "1.0.0"
}
```

### Documentación Interactiva

Una vez ejecutado el servidor, accede a:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🛠️ Stack Tecnológico

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.11+ | Lenguaje base |
| **FastAPI** | Latest | Framework web async |
| **LangChain** | Latest | Orquestación de LLMs |
| **LangGraph** | Latest | Agentes de IA |
| **Anthropic Claude** | claude-sonnet-4-5-20250929 | Modelo de lenguaje |
| **Pydantic** | v2 | Validación de datos |
| **Uvicorn** | Latest | Servidor ASGI |

---

## 🔒 Seguridad

- **CORS:** Configura `ALLOWED_ORIGINS` en producción
- **API Keys:** Nunca expongas las claves de API en el código
- **Rate Limiting:** Implementar en producción según necesidades
- **HTTPS:** Usar siempre en producción

---

## 🗺️ Roadmap

- [x] Módulo HSE - Análisis 5 Porqués
- [x] Chatbot Estandarización - Core Lógico (Agents & Tools)
- [x] Framework de Pruebas Multi-Agente (Simulación)
- [x] Evaluador Automático (LLM-as-a-Judge)
- [ ] Integración final con API Defontana (ERP)
- [ ] Dashboard de métricas de IA
