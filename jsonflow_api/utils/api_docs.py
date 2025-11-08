"""
api_docs.py

Génération automatique de documentation Markdown pour une application FastAPI.

Ce module se concentre sur la **mise en forme lisible** de la documentation,
à partir des données techniques extraites par `introspection.py`.

Contenu principal :
- _format_example_block : formate les exemples JSON
- _describe_single_endpoint : construit la description Markdown d’un endpoint
- generate_endpoints_section : assemble la section des endpoints
- _generate_models_section : assemble la section des modèles Pydantic
- generate_markdown_doc_complete : produit la documentation complète en Markdown
"""

from fastapi import FastAPI
from typing import List, Type
from pydantic import BaseModel
from .introspection import (
    get_all_endpoints,
    collect_models_from_endpoints,
    _get_model_info,
    extract_model_examples,
    _get_model_by_name
)
import json

# =========================
# --- UTILITAIRES
# =========================

def _format_example_block(examples: List[dict]) -> List[str]:
    """
    Formate une liste d'exemples JSON en bloc Markdown.

    Args:
        examples (List[dict]): Liste d’exemples JSON à afficher.

    Returns:
        List[str]: Lignes de texte Markdown incluant les blocs de code formatés.
    """
    lines = []
    if examples:
        lines.append("#### Exemples :")
        for ex in examples:
            json_str = json.dumps(ex, indent=2, ensure_ascii=False)
            lines.append(f"```json\n{json_str}\n```")
    return lines

# =========================
# --- ENDPOINTS
# =========================

def _describe_single_endpoint(ep: dict, app: FastAPI) -> List[str]:
    """
    Construit la description Markdown d’un endpoint FastAPI.

    Args:
        ep (dict): Dictionnaire contenant les métadonnées de l’endpoint
                   (path, methods, summary, parameters, body_model, etc.)
        app (FastAPI): Application FastAPI pour la résolution des modèles Pydantic.

    Returns:
        List[str]: Lignes Markdown décrivant l’endpoint (méthodes, paramètres, corps, exemples).
    """
    lines = [f"### {', '.join(ep.get('methods', []))} {ep.get('path')}"]

    # --- Résumé et description
    if ep.get("summary"):
        lines.append(f"**Résumé :** {ep['summary']}")
    if ep.get("description"):
        lines.append(f"**Description :** {ep['description']}")

    # --- Paramètres génériques (path / query)
    params = ep.get("parameters", [])
    if params:
        lines.append("**Paramètres :**")
        for p in params:
            name = p.get("name", "unknown")
            location = p.get("in", "query")
            param_type = p.get("type", "unknown")
            required = p.get("required", False)
            desc = p.get("description", "")
            lines.append(
                f"- `{name}` ({location}, type `{param_type}`, required={required}) {desc}"
            )

    # --- Corps (body)
    body_model_name = ep.get("body_model")
    if body_model_name:
        model = _get_model_by_name(app, body_model_name)
        if model:
            lines.append("**Corps attendu :**")
            examples = extract_model_examples(model)
            if examples:
                lines += _format_example_block(examples)
            else:
                lines.append(f"`{model.__name__}`")

    return lines

def generate_endpoints_section(endpoints: List[dict], app: FastAPI) -> dict:
    """
    Génère la section complète Markdown listant les endpoints de l'API.

    Args:
        endpoints (List[dict]): Liste des endpoints collectés via introspection.
        app (FastAPI): Application FastAPI associée.

    Returns:
        dict: Structure de section Markdown contenant le titre et le contenu.
    """
    section = {"title": "Endpoints", "content": []}
    for ep in endpoints:
        section["content"] += _describe_single_endpoint(ep, app) + [""]
    return section

# =========================
# --- MODÈLES PYDANTIC
# =========================

def _generate_models_section(models: List[Type[BaseModel]]) -> dict:
    """
    Génère la section Markdown pour les modèles Pydantic détectés.

    Inclut les exemples JSON et les règles métier s’ils existent.

    Args:
        models (List[Type[BaseModel]]): Liste des classes Pydantic utilisées par l’API.

    Returns:
        dict: Section Markdown décrivant les modèles.
    """
    section = {"title": "Modèles Pydantic", "content": []}

    for model in models:
        info = _get_model_info(model)
        section["content"].append(f"## Modèle `{model.__name__}`")

        # --- Exemples
        if info.get("examples"):
            section["content"] += _format_example_block(info["examples"])

        # --- Règles métier
        if info.get("business_rules"):
            section["content"] += info["business_rules"]

        section["content"].append("")  # ligne vide de séparation

    return section

# =========================
# --- DOCUMENTATION COMPLÈTE
# =========================

def _generate_quick_links_section() -> dict:
    """
    Génère une section Markdown contenant des liens rapides vers l'API.

    Returns:
        dict: Dictionnaire avec le titre de la section et le contenu Markdown sous forme de liste de chaînes.
    """
    links = [
        ("Swagger UI", "http://127.0.0.1:8000/docs"),
        ("ReDoc", "http://127.0.0.1:8000/redoc"),
        ("Markdown JSON", "http://127.0.0.1:8000/markdown-docs"),
        ("Schéma détaillé JSON", "http://127.0.0.1:8000/schema-detailed"),
        ("Liste des modèles Pydantic", "http://127.0.0.1:8000/models"),
        ("Documentation endpoints", "http://127.0.0.1:8000/documentation-endpoints"),
        ("Liste des endpoints", "http://127.0.0.1:8000/endpoints"),
        ("Vérification santé API", "http://127.0.0.1:8000/health"),
    ]
    lines = ["## Liens rapides"]
    for name, url in links:
        lines.append(f"- [{name}]({url})")
    return {"title": "Liens rapides", "content": lines}

def generate_markdown_doc_complete(app: FastAPI) -> dict:
    """
    Construit la documentation complète de l'application FastAPI en Markdown.

    Combine la section des modèles Pydantic et celle des endpoints.

    Args:
        app (FastAPI): Application FastAPI à documenter.

    Returns:
        dict: Structure complète de documentation avec plusieurs sections Markdown.
    """
    endpoints = get_all_endpoints(app)
    models = collect_models_from_endpoints(app)

    models_section = _generate_models_section(models)
    endpoints_section = generate_endpoints_section(endpoints, app)

    return {
        "title": "Documentation de l'API",
        "sections": [_generate_quick_links_section(), models_section, endpoints_section],
    }