import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import hse, articulo
# from app.routers import rrhh  <-- Descomentarás esto cuando crees el módulo de RRHH

# Cargar variables de entorno
load_dotenv()

# 1. Configuración de la Aplicación
app = FastAPI(
    title="ControlWorldMS AI Service",
    description="Microservicio de IA con LangChain para Laravel",
    version="1.0.0"
)

# 2. Configuración de CORS (Seguridad)
# Determinar orígenes permitidos según entorno
app_env = os.getenv("APP_ENV", "local")
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")

if app_env == "production":
    if allowed_origins_str:
        origins = [origin.strip() for origin in allowed_origins_str.split(",")]
    else:
        # Fallback seguro o advertencia en logs
        origins = [] 
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Registro de Rutas (Routers)
# Aquí le dices a FastAPI: "Todo lo que esté en hse.py, ponlo bajo la url /hse"
app.include_router(hse.router, prefix="/hse", tags=["HSE"])
app.include_router(articulo.router, prefix="/articulo", tags=["Articulos"])

# app.include_router(rrhh.router, prefix="/rrhh", tags=["RRHH"]) <-- Futuro módulo

# 4. Ruta de prueba (Health Check)
@app.get("/")
def root():
    return {
        "status": "online", 
        "service": "ControlWorldMS AI",
        "version": "1.0.0"
    }

# Nota: No necesitas poner 'if __name__ == "__main__"' porque usaremos Gunicorn/Uvicorn para correrlo.