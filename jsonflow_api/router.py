"""
router.py

Définition des routes principales de l'API JsonFlow.
Inclut :
- Endpoint de commande robot
- Endpoints pour la documentation et introspection
- Endpoint de santé
"""

from fastapi import APIRouter, Request, Body
from typing import List, Type
from .models import JsonCommand
from .utils.api_docs import generate_markdown_doc_complete, generate_endpoints_section
from .utils.introspection import (
    get_all_endpoints,
    collect_models_from_endpoints
)

__all__ = [
    "get_router",
]


def get_router() -> APIRouter:
    """
    Retourne un APIRouter configuré avec tous les endpoints principaux de l'API.

    Endpoints inclus :
        - POST /command : Valide et retourne une commande robot
        - GET /endpoints : Liste tous les endpoints de l'API
        - GET /models : Liste tous les modèles utilisés
        - GET /documentation-endpoints : Documentation lisible des endpoints
        - GET /markdown-docs : Documentation complète au format Markdown JSON
        - GET /schema-detailed : Schéma détaillé des endpoints
        - GET /health : Vérification de santé de l'API
    """
    router = APIRouter()

    # ======================
    # Endpoint : Commande robot
    # ======================
    @router.post("/command")
    async def post_command(cmd: JsonCommand = Body(...)):
        """
        Valide et retourne la commande robot.

        Args:
            cmd (JsonCommand): Payload JSON correspondant à la commande

        Returns:
            dict: Confirmation et données de la commande validée
        """
        return {"message": "✅ Commande validée", "data": cmd.model_dump()}

    # ======================
    # Endpoints d'introspection
    # ======================
    @router.get("/endpoints")
    async def list_endpoints(request: Request):
        """
        Retourne la liste de tous les endpoints de l'application FastAPI.

        Args:
            request (Request): Objet FastAPI request pour accéder à app

        Returns:
            dict: Liste des endpoints
        """
        endpoints = get_all_endpoints(request.app)
        return {"endpoints": endpoints}

    @router.get("/models")
    async def get_models(request: Request):
        """
        Retourne tous les modèles Pydantic utilisés dans les endpoints.

        Args:
            request (Request): Objet FastAPI request pour accéder à app

        Returns:
            dict: Liste des noms de modèles
        """
        models: List[Type] = collect_models_from_endpoints(request.app)
        return {"models": [model.__name__ for model in models]}

    # ======================
    # Endpoints documentation
    # ======================
    @router.get("/documentation-endpoints")
    async def get_endpoints_docs(request: Request):
        """
        Retourne une documentation lisible des endpoints.

        Args:
            request (Request): Objet FastAPI request pour accéder à app

        Returns:
            dict: Documentation des endpoints (titre + contenu)
        """
        endpoints = get_all_endpoints(request.app)
        return generate_endpoints_section(endpoints, request.app)

    @router.get("/markdown-docs")
    async def markdown_docs(request: Request):
        """
        Retourne la documentation complète au format Markdown JSON.

        Args:
            request (Request): Objet FastAPI request pour accéder à app

        Returns:
            dict: Documentation complète (sections modèles + endpoints)
        """
        return generate_markdown_doc_complete(request.app)

    @router.get("/schema-detailed")
    async def schema_detailed(request: Request):
        """
        Retourne un schéma détaillé de tous les endpoints, incluant paramètres et body.

        Args:
            request (Request): Objet FastAPI request pour accéder à app

        Returns:
            dict: Endpoints avec détails sur params, query et body
        """
        return {"endpoints": get_all_endpoints(request.app)}

    # ======================
    # Endpoint de santé
    # ======================
    @router.get("/health")
    async def health(request: Request):
        """
        Endpoint de vérification de santé de l'API.

        Args:
            request (Request): Objet FastAPI request pour accéder à app

        Returns:
            dict: Status et version de l'application
        """
        return {"status": "ok", "version": getattr(request.app, "version", "unknown")}

    return router
