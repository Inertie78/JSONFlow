"""
test/test_jsonflow_api.py

Tests complets pour JSONFlow API (modèle + endpoints).

- Valide le modèle Pydantic JsonCommand (logique métier, timestamps, fuseaux horaires)
- Vérifie les endpoints principaux de l’API FastAPI via TestClient (aucun serveur externe requis)
"""

import math
import pytest
from fastapi.testclient import TestClient

from jsonflow_api.main import app
from jsonflow_api.models import JsonCommand
from jsonflow_api.config.settings import DEFAULT_TZ


# Client FastAPI pour tests en mémoire
client = TestClient(app)


# ==========================================================
# TESTS UNITAIRES : Modèle JsonCommand
# ==========================================================

def test_move_command_valid():
    """Vérifie la création valide d'une commande de type 'move'."""
    payload = {"command": "move", "direction": "forward", "speed": 0.5, "duration": 5}
    cmd = JsonCommand(**payload)
    assert cmd.command == "move"
    assert cmd.direction == "forward"
    assert math.isclose(cmd.speed, 0.5, rel_tol=1e-9)
    assert cmd.duration == 5
    assert cmd.timestamp is not None
    assert cmd.tz == DEFAULT_TZ


def test_move_command_missing_fields():
    """Vérifie qu'une commande 'move' sans direction/speed lève une exception."""
    payload = {"command": "move"}
    with pytest.raises(Exception) as exc:
        JsonCommand(**payload)
    assert "direction" in str(exc.value) or "speed" in str(exc.value)


def test_move_command_auto_speed_limit():
    """Vérifie que la vitesse maximale en mode 'auto' est respectée."""
    payload = {"command": "move", "direction": "backward", "speed": 0.8, "mode": "auto"}
    with pytest.raises(Exception) as exc:
        JsonCommand(**payload)
    assert "vitesse maximale" in str(exc.value) or "auto" in str(exc.value)


def test_move_command_duration_limit():
    """Vérifie que la durée maximale d'une commande 'move' est respectée."""
    payload = {"command": "move", "direction": "left", "speed": 0.5, "duration": 15}
    with pytest.raises(Exception) as exc:
        JsonCommand(**payload)
    assert "duration" in str(exc.value) or "durée" in str(exc.value)


def test_sensor_command_valid():
    """Vérifie la création valide d'une commande de type 'sensor'."""
    payload = {"command": "sensor", "sensor_type": "temperature"}
    cmd = JsonCommand(**payload)
    assert cmd.command == "sensor"
    assert cmd.sensor_type == "temperature"


def test_sensor_command_missing_type():
    """Vérifie qu'une commande 'sensor' sans type lève une exception."""
    payload = {"command": "sensor"}
    with pytest.raises(Exception) as exc:
        JsonCommand(**payload)
    assert "sensor_type" in str(exc.value)


def test_timestamp_auto_addition():
    """Vérifie que le timestamp est automatiquement ajouté si absent."""
    payload = {"command": "sensor", "sensor_type": "humidity"}
    cmd = JsonCommand(**payload)
    assert cmd.timestamp is not None
    assert "T" in cmd.timestamp


def test_custom_timezone():
    """Vérifie que le fuseau horaire personnalisé est pris en compte."""
    payload = {"command": "sensor", "sensor_type": "pressure", "tz": "Europe/Paris"}
    cmd = JsonCommand(**payload)
    assert cmd.tz == "Europe/Paris"
    assert "T" in cmd.timestamp


def test_business_rules_defined():
    """Vérifie que des règles métier sont définies pour le modèle."""
    rules = JsonCommand.business_rules()
    assert isinstance(rules, list)
    assert len(rules) > 0
    assert any("validate" in rule for rule in rules)


def test_examples_non_empty():
    """Vérifie que des exemples sont définis pour la documentation."""
    examples = JsonCommand.get_examples()
    assert isinstance(examples, list)
    assert len(examples) > 0


# ==========================================================
# TESTS D’INTÉGRATION : Endpoints FastAPI
# ==========================================================

def contient_erreur(response, message: str) -> bool:
    """Recherche une sous-chaîne dans le champ 'detail' d'une réponse JSON d'erreur."""
    try:
        detail = response.json().get("detail", [])
        if isinstance(detail, str):
            return message in detail
        return any(
            message in (err.get("msg", err) if isinstance(err, dict) else str(err))
            for err in detail
        )
    except Exception:
        return False


def test_post_command_valid():
    """Vérifie que l’endpoint /command accepte une commande valide."""
    payload = {"command": "move", "direction": "forward", "speed": 0.4, "duration": 5}
    response = client.post("/command", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["command"] == "move"
    assert data["direction"] == "forward"
    assert math.isclose(data["speed"], 0.4, rel_tol=1e-9)
    assert "timestamp" in data


def test_post_command_invalid_sensor():
    """Vérifie qu'une commande sensor sans sensor_type retourne une erreur 400."""
    payload = {"command": "sensor", "timestamp": "2025-10-29T18:30:00+00:00"}
    response = client.post("/command", json=payload)
    assert response.status_code == 400
    assert contient_erreur(response, "sensor_type")


def test_post_command_invalid_duration():
    """Vérifie qu'une commande 'move' avec une durée trop longue retourne une erreur."""
    payload = {"command": "move", "direction": "forward", "speed": 0.8, "duration": 15}
    response = client.post("/command", json=payload)
    assert response.status_code == 400
    assert contient_erreur(response, "duration")


def test_post_command_auto_too_fast():
    """Vérifie qu'en mode 'auto', la vitesse max est respectée."""
    payload = {"command": "move", "direction": "forward", "speed": 0.9, "mode": "auto"}
    response = client.post("/command", json=payload)
    assert response.status_code == 400
    assert contient_erreur(response, "auto") or contient_erreur(response, "vitesse")


def test_get_markdown_docs():
    """Vérifie la génération de la documentation Markdown."""
    response = client.get("/markdown-docs")
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert any("Endpoints" in section["title"] for section in data["sections"])


def test_get_schema_detailed():
    """Vérifie le schéma détaillé des endpoints."""
    response = client.get("/schema-detailed")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data
    assert isinstance(data["endpoints"], list)
    assert any(ep["path"] == "/markdown-docs" for ep in data["endpoints"])


def test_healthcheck():
    """Vérifie que l’endpoint /health fonctionne."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data