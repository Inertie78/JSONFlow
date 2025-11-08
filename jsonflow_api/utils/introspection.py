"""
introspection.py

Outils d’introspection pour une application FastAPI :
permettent d’extraire automatiquement les informations sur
les endpoints, les modèles Pydantic et leurs exemples ou règles métier.

Contenu principal :
- get_all_endpoints : récupère la liste des endpoints FastAPI
- collect_models_from_endpoints : collecte les modèles Pydantic utilisés
- extract_model_examples / _get_model_info : extrait exemples et règles métier
- _get_model_by_name : recherche un modèle Pydantic par nom
"""

from typing import Any, Dict, List, Type, Optional
from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel
import json


# =========================
# --- UTILITAIRES GÉNÉRAUX
# =========================

def _format_param_type(param: Any) -> str:
    """
    Retourne le type d’un paramètre sous forme de chaîne lisible.

    Args:
        param (Any): Objet représentant un paramètre FastAPI.

    Returns:
        str: Nom du type détecté (ex: 'str', 'int', 'float').
    """
    try:
        return param.type_.__name__
    except AttributeError:
        return str(getattr(param, "type_", type(param)))


def extract_model_examples(model: Type[BaseModel]) -> List[dict]:
    """
    Extrait les exemples JSON d’un modèle Pydantic, s’ils existent.

    Args:
        model (Type[BaseModel]): Classe Pydantic à inspecter.

    Returns:
        List[dict]: Liste d’exemples JSON, vide si non définis.
    """
    if hasattr(model, "get_examples"):
        return model.get_examples()
    return []


def _generate_business_rules_section(model: Type[BaseModel]) -> List[str]:
    """
    Extrait les règles métier associées à un modèle Pydantic.

    Args:
        model (Type[BaseModel]): Modèle à analyser.

    Returns:
        List[str]: Lignes Markdown listant les règles métier.
    """
    lines = []
    rules = getattr(model, "business_rules", lambda: [])()
    if rules:
        lines.append("#### Règles métier :")
        for r in rules:
            lines.append(f"- {r}")
    return lines


def _get_model_info(model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Regroupe les informations descriptives d’un modèle Pydantic.

    Inclut ses exemples JSON et ses éventuelles règles métier.

    Args:
        model (Type[BaseModel]): Modèle Pydantic à analyser.

    Returns:
        Dict[str, Any]: Dictionnaire avec clés 'examples' et 'business_rules'.
    """
    info: Dict[str, Any] = {}
    examples = extract_model_examples(model)
    if examples:
        info["examples"] = examples
    business_rules = _generate_business_rules_section(model)
    if business_rules:
        info["business_rules"] = business_rules
    return info


# =========================
# --- ENDPOINTS INTROSPECTION
# =========================

def get_all_endpoints(app: FastAPI) -> List[dict]:
    """
    Retourne les informations de tous les endpoints déclarés dans l’application FastAPI.

    Args:
        app (FastAPI): Application FastAPI à inspecter.

    Returns:
        List[dict]: Liste d’endpoints avec leurs métadonnées principales.
    """
    endpoints = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            endpoint_info = _extract_endpoint_info(route)
            endpoints.append(endpoint_info)
    return endpoints


def _extract_endpoint_info(route: APIRoute) -> dict:
    """
    Extrait les métadonnées principales d’un endpoint FastAPI.

    Inclut :
      - chemin (`path`)
      - méthodes HTTP
      - modèle du corps (`body_model`)
      - modèle de réponse (`response_model`)
      - paramètres de chemin

    Args:
        route (APIRoute): Route FastAPI à analyser.

    Returns:
        dict: Dictionnaire contenant les informations de l’endpoint.
    """
    endpoint_info = {
        "path": route.path,
        "methods": list(route.methods),
        "summary": getattr(route, "summary", None),
        "description": getattr(route, "description", None),
        "parameters": [],
        "body_model": None,
        "response_model": getattr(route, "response_model", None),
    }

    # --- Paramètres de chemin (path)
    for param in getattr(route.dependant, "path_params", []):
        endpoint_info["parameters"].append({
            "name": getattr(param, "name", "unknown"),
            "type": _format_param_type(param),
            "required": getattr(param, "required", False),
            "in": "path"
        })

    # --- Paramètre du corps (body)
    for body_param in getattr(route.dependant, "body_params", []):
        t = getattr(body_param, "type_", None)
        if isinstance(t, type) and issubclass(t, BaseModel):
            endpoint_info["body_model"] = t.__name__

    return endpoint_info


# =========================
# --- GESTION DES MODÈLES PYDANTIC
# =========================

def _is_target_model(obj: Any, name: str) -> Optional[Type[BaseModel]]:
    """
    Vérifie si un objet est un modèle Pydantic portant le nom spécifié.

    Args:
        obj (Any): Objet à tester.
        name (str): Nom du modèle recherché.

    Returns:
        Optional[Type[BaseModel]]: Le modèle trouvé ou None.
    """
    if isinstance(obj, type) and issubclass(obj, BaseModel) and obj.__name__ == name:
        return obj
    return None


def _search_in_app_models(app: FastAPI, name: str) -> Optional[Type[BaseModel]]:
    """
    Recherche un modèle dans la liste `app.models` si elle existe.

    Args:
        app (FastAPI): Application FastAPI contenant éventuellement une liste de modèles.
        name (str): Nom du modèle recherché.

    Returns:
        Optional[Type[BaseModel]]: Le modèle trouvé ou None.
    """
    if hasattr(app, "models"):
        for candidate in app.models:
            model = _is_target_model(candidate, name)
            if model:
                return model
    return None


def _search_in_route_models(route: APIRoute, name: str) -> Optional[Type[BaseModel]]:
    """
    Recherche un modèle dans les paramètres de corps et les modèles de réponse d’une route.

    Args:
        route (APIRoute): Route FastAPI à analyser.
        name (str): Nom du modèle recherché.

    Returns:
        Optional[Type[BaseModel]]: Le modèle trouvé ou None.
    """
    for body_param in getattr(route.dependant, "body_params", []):
        model = _is_target_model(getattr(body_param, "type_", None), name)
        if model:
            return model
    return _is_target_model(getattr(route, "response_model", None), name)


def _get_model_by_name(app: FastAPI, name: str) -> Optional[Type[BaseModel]]:
    """
    Recherche un modèle Pydantic par son nom au sein de l’application.

    La recherche se fait d’abord dans `app.models`, puis dans les routes.

    Args:
        app (FastAPI): Application FastAPI à explorer.
        name (str): Nom du modèle recherché.

    Returns:
        Optional[Type[BaseModel]]: Classe du modèle si trouvée, sinon None.
    """
    # --- Recherche dans app.models
    model = _search_in_app_models(app, name)
    if model:
        return model

    # --- Recherche dans les routes
    for route in (r for r in app.routes if isinstance(r, APIRoute)):
        model = _search_in_route_models(route, name)
        if model:
            return model

    return None


def collect_models_from_endpoints(app: FastAPI) -> List[Type[BaseModel]]:
    """
    Collecte l’ensemble des modèles Pydantic utilisés dans les endpoints de l’API.

    Args:
        app (FastAPI): Application FastAPI à inspecter.

    Returns:
        List[Type[BaseModel]]: Liste unique des modèles Pydantic détectés.
    """
    endpoints = get_all_endpoints(app)
    models_set: set[Type[BaseModel]] = set()

    for ep in endpoints:
        for key in ("body_model", "response_model"):
            model_name = ep.get(key)
            if model_name:
                model = _get_model_by_name(app, model_name)
                if model:
                    models_set.add(model)

    return list(models_set)
