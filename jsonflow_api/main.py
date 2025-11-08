"""
main.py

Point d’entrée principal de l’application FastAPI pour le projet JsonFlow.

Ce module initialise :
- l’application FastAPI,
- les modèles Pydantic disponibles,
- et les routes de l’API (endpoints).

Il constitue le point central de démarrage du service REST.
"""

from fastapi import FastAPI
from .models import JsonCommand
from .router import get_router


# =========================
# --- INITIALISATION DE L’APPLICATION
# =========================

app = FastAPI(
    title="jsonflow_api – API REST pour robot modulaire",
    description=(
        "Cadre générique pour valider des structures JSON et générer leur documentation automatiquement."
    ),
    version="1.4",
    docs_url="/docs",        # Interface Swagger UI
    redoc_url="/redoc",      # Interface ReDoc
    openapi_url="/openapi.json",  # Export du schéma OpenAPI
)


# =========================
# --- DÉCLARATION DES MODÈLES
# =========================

# Liste centralisée des modèles Pydantic utilisés dans l'application.
# Cette liste est utilisée par les modules d’introspection et de génération documentaire.
app.models = [
    JsonCommand,  # Modèle principal des commandes du robot JsonFlow
]


# =========================
# --- ROUTER PRINCIPAL
# =========================

# Import et inclusion du router principal contenant les endpoints de contrôle du robot.
router = get_router()
app.include_router(router)


# =========================
# --- POINT D’ENTRÉE (LOCAL DEV)
# =========================

if __name__ == "__main__":
    import uvicorn

    # Démarre le serveur en mode développement avec rechargement automatique.
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
