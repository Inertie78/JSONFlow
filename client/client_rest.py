"""
client_rest.py

Client REST pour l'API JSONFlow avec tests automatisés.

Ce module permet :
1. D'envoyer des commandes à l'API (/command).
2. De récupérer la documentation Markdown (/markdown-docs) et le schéma (/schema-detailed).
3. De tester automatiquement la validation des payloads, la gestion des erreurs,
   ainsi que les règles métier spécifiques (vitesse max, duration, auto mode...).

Dépendances :
- httpx
- math
- json
"""

import httpx
import math
import json

# === 🔗 Configuration centralisée des endpoints ===
API_BASE = "http://localhost:8000/"
VERBOSE = True  # Pour désactiver les prints en CI/CD

ENDPOINTS = {
    "command": "command",
    "markdown-docs": "markdown-docs",
    "schema-detailed": "schema-detailed"
}

# === 🔹 Helpers ===

def afficher_resultat(response: httpx.Response):
    """
    Affiche le statut HTTP et le contenu de la réponse.

    Args:
        response (httpx.Response): Réponse HTTP reçue.
    """
    if not VERBOSE:
        return
    print(f"Status code: {response.status_code}")
    try:
        print("Réponse JSON:")
        print(response.json())
    except Exception:
        print("Réponse brute:")
        print(response.text)

def contient_erreur(response: httpx.Response, message: str) -> bool:
    """
    Vérifie si un message d'erreur spécifique est présent dans la réponse.

    Args:
        response (httpx.Response): Réponse HTTP.
        message (str): Message d'erreur attendu.

    Returns:
        bool: True si le message est trouvé, False sinon.
    """
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

# === 🧪 Tests ===

def test_commande_valide(client: httpx.Client):
    """
    Teste une commande 'move' valide avec tous les paramètres requis.
    Vérifie que la réponse est un succès et que les données sont cohérentes.
    """
    payload = {
        "command": "move",
        "direction": "forward",
        "speed": 0.4,
        "duration": 5,
        "mode": "auto"
    }
    response = client.post(ENDPOINTS["command"], json=payload)
    print("\n✅ Test: Commande valide")
    afficher_resultat(response)
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["message"].startswith("✅ Commande validée")
    assert json_resp["data"]["direction"] == "forward"
    assert math.isclose(json_resp["data"]["speed"], 0.4, rel_tol=1e-9)
    assert json_resp["data"]["duration"] == 5
    assert "timestamp" in json_resp["data"]

def test_commande_move_sans_direction(client: httpx.Client):
    """
    Teste une commande 'move' sans direction.
    Vérifie que l'API retourne une erreur liée à la direction ou à la vitesse.
    """
    payload = {"command": "move", "speed": 0.8, "duration": 5}
    response = client.post(ENDPOINTS["command"], json=payload)
    print("\n❌ Test: move sans direction")
    afficher_resultat(response)
    assert contient_erreur(response, "direction") or contient_erreur(response, "speed")

def test_commande_sensor_sans_type(client: httpx.Client):
    """
    Teste une commande 'sensor' sans 'sensor_type'.
    Vérifie que l'API retourne une erreur appropriée.
    """
    payload = {"command": "sensor", "timestamp": "2025-10-29T18:30:00"}
    response = client.post(ENDPOINTS["command"], json=payload)
    print("\n❌ Test: sensor sans sensor_type")
    afficher_resultat(response)
    assert contient_erreur(response, "sensor_type")

def test_commande_timestamp_invalide(client: httpx.Client):
    """
    Teste une commande avec un timestamp invalide.
    Vérifie que l'API détecte le format incorrect.
    """
    payload = {
        "command": "move",
        "direction": "forward",
        "speed": 0.8,
        "duration": 5,
        "timestamp": "not-a-date"
    }
    response = client.post(ENDPOINTS["command"], json=payload)
    print("\n❌ Test: timestamp invalide")
    afficher_resultat(response)
    assert contient_erreur(response, "timestamp")

def test_commande_duration_trop_longue(client: httpx.Client):
    """
    Teste une commande 'move' avec une durée trop longue (>10s).
    Vérifie que l'API retourne une erreur de validation.
    """
    payload = {"command": "move", "direction": "forward", "speed": 0.8, "duration": 15}
    response = client.post(ENDPOINTS["command"], json=payload)
    print("\n❌ Test: duration > 10")
    afficher_resultat(response)
    assert contient_erreur(response, "durée") or contient_erreur(response, "duration")

def test_commande_auto_trop_rapide(client: httpx.Client):
    """
    Teste une commande 'auto' avec une vitesse trop élevée (>0.5).
    Vérifie que l'API applique la règle métier.
    """
    payload = {"command": "move", "direction": "forward", "speed": 0.9, "mode": "auto"}
    response = client.post(ENDPOINTS["command"], json=payload)
    print("\n❌ Test: auto mode avec speed > 0.5")
    afficher_resultat(response)
    assert contient_erreur(response, "auto") and contient_erreur(response, "vitesse")

def test_markdown_docs(client: httpx.Client):
    """
    Teste la récupération de la documentation Markdown complète.

    Returns:
        list: Liste des sections Markdown.
    """
    response = client.get(ENDPOINTS["markdown-docs"])
    print("\n📄 Test: récupération de /markdown-docs")
    afficher_resultat(response)
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    return data["sections"]

def test_schema_docs(client: httpx.Client):
    """
    Teste la récupération du schéma détaillé des endpoints.

    Returns:
        dict: Schéma JSON des endpoints.
    """
    response = client.get(ENDPOINTS["schema-detailed"])
    print("\n📄 Test: récupération de /schema-detailed")
    afficher_resultat(response)
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data
    assert isinstance(data["endpoints"], list)
    assert any(ep["path"] == "/markdown-docs" for ep in data["endpoints"])
    return data

def enregistrer_resultats_dans_fichier(client: httpx.Client):
    """
    Exécute les tests de documentation et enregistre les résultats dans un fichier Markdown.
    Corrige :
    - les blocs ``` imbriqués,
    - les doublons de titres,
    - et ajoute une mise en forme cohérente et stable.
    """
    md_sections = test_markdown_docs(client)
    schema_data = test_schema_docs(client)

    with open("README_JSONFLOW.md", "w", encoding="utf-8") as file:
        file.write("# Résultats des Tests de l'API JSONFlow\n\n")
        file.write("## Test 1: Documentation Markdown (/markdown-docs)\n\n")

        for section in md_sections:
            title = section.get("title", "Section sans titre").strip()
            content_lines = section.get("content", [])
            content = "\n".join(content_lines).strip()

            # Évite les doublons : n’ajoute pas de titre si le contenu commence déjà par "#"
            if not content.startswith("#"):
                file.write(f"### {title}\n\n")

            # Écrit directement le contenu Markdown sans wrapper ```markdown
            file.write(content)
            file.write("\n\n---\n\n")

        # Section Schéma
        file.write("## Test 2: Schéma détaillé (/schema-detailed)\n\n")
        file.write("```json\n")
        file.write(json.dumps(schema_data, indent=2, ensure_ascii=False))
        file.write("\n```\n")
    
    print("\n🎯 Tous les tests ont été exécutés avec succès. Résultats enregistrés dans README_JSONFLOW.md ✅")
    print("\n✅ Les résultats des tests ont été enregistrés dans 'README_JSONFLOW.md'.")

# === 🔹 Exécution directe ===
if __name__ == "__main__":
    try:
        with httpx.Client(base_url=API_BASE, timeout=10.0) as client:
            tests = [
                test_commande_valide,
                test_commande_move_sans_direction,
                test_commande_sensor_sans_type,
                test_commande_timestamp_invalide,
                test_commande_duration_trop_longue,
                test_commande_auto_trop_rapide,
                enregistrer_resultats_dans_fichier
            ]

            for test in tests:
                test(client)
    except httpx.RequestError as e:
        print(f"🚨 Impossible de contacter l’API JSONFlow à {API_BASE}")
        print(f"Détail de l’erreur : {e}")