# 🧩 JSONFlow – API REST générique de validation et documentation JSON

## Description

JSONFlow est une API REST générique basée sur FastAPI.
Elle permet de valider, documenter et exécuter dynamiquement des structures JSON, selon des modèles Pydantic configurables.

Ce projet est conçu pour être utilisé dans divers contextes :

- Contrôle d’équipements (robots, capteurs, IoT, etc.)
- Validation de données métier
- API de configuration ou de simulation
- Plateforme d’intégration JSON (tests, ingestion, etc.)

## Fonctionnalités

**✅ Validation JSON dynamique** : Vérifie automatiquement la cohérence des données selon les modèles Pydantic.

**🧩 Règles métier personnalisables** : Chaque modèle peut définir ses propres validations (validate_logic, business_rules).

**🌍 Fuseau horaire dynamique** : Gère les timestamps ISO 8601 avec timezone, configurable via .env.

**📘 Documentation automatique** : Génère une documentation complète en Markdown ou via Swagger/ReDoc.

**🔍 Introspection complète de l’API** : Liste dynamique des endpoints et des modèles utilisés.

## Installation

### Prérequis

- Python 3.9+
- pip (gestionnaire de paquets Python)
- Un fichier `.env` configuré avec les variables nécessaires

```env
DEFAULT_TZ=UTC
```

## ⚙️ Étapes d'installation

1. **Clonez ce dépôt :**

  ```bash
  git clone https://github.com/votre-utilisateur/jsonflow-api.git
  cd jsonflow-api
  ```

2. Lancement rapide du projet :

- Sous Windows
  Utilise le script suivant pour créer l’environnement virtuel, installer les dépendances, lancer le serveur FastAPI et exécuter les tests :

```bat
start_jsonflow.bat
```

- Sous Linux/macOS
Utilise le script shell équivalent :

```sh
bash start_jsonflow.sh
```

>Ces scripts :
créent automatiquement un environnement virtuel .venv s’il n’existe pas
installent les paquets nécessaires (fastapi, uvicorn, httpx)
lancent le serveur FastAPI (uvicorn jsonflow_api.main:app --reload)
ouvrent un second terminal pour exécuter client_rest.py (tests manuels)

💡 *Vous pouvez également exécuter manuellement le serveur avec :*

```bash
uvicorn jsonflow_api.main:app --reload
```

---

## 🚀 Points d'API

- L’API offre plusieurs endpoints pour valider, explorer et documenter des structures JSON dynamiques :

### POST /command

- Voici comment envoyer une structure JSON de type commande :
- Body : Doit être un objet JSON respectant le modèle JsonCommand.

- Exemple de commande :

```json
{
  "command": "move",
  "direction": "forward",
  "speed": 0.5,
  "duration": 5
}
```

- Réponse :

```json
{
  "message": "✅ Commande validée",
  "data": {
    "command": "move",
    "direction": "forward",
    "speed": 0.5,
    "duration": 5,
    "timestamp": "2025-11-06T10:30:00+00:00",
    "tz": "UTC",
    "mode": "manual"
  }
}
```

### GET /endpoints

- Description : Retourne la liste de tous les endpoints de l'API sous forme lisible.

### GET /models

- Description : Retourne les modèles Pydantic utilisés dans l'API.

### GET /documentation-endpoints

- Description : Retourne la documentation des endpoints de l'API.

### GET /markdown-docs

- Description : Retourne la documentation complète au format Markdown.

### GET /schema-detailed

 -Description : Retourne un schéma détaillé des endpoints (paramètres + body).

### GET /health

- Description : Point de vérification de santé de l'API pour s'assurer que l'API fonctionne correctement.

## 🧱 Structure du Projet

Voici un aperçu de la structure des fichiers du projet :

```tree
JSONFlow/
├── __init__.py               # Fichier d'initialisation du package JSONFlow
├── jsonflow_api/
│   ├── __init__.py           # Fichier d'initialisation du package
│   ├── main.py               # Point d’entrée de l’application FastAPI (titre & description adaptés)
│   ├── models.py             # Modèles de validation JSON (ex : JsonCommand)
│   ├── router.py             # Définition des routes principales
│   ├── utils/                # Utilitaires (documentation, introspection)
│   │   ├── api_docs.py       # Génération Markdown et sections Swagger
│   │   ├── introspection.py  # Extraction, parsing, logique d’analyse
│   │   └── __init__.py       # Initialisation du module utils
│   ├── config/               # Configuration de l’application
│   │   ├── __init__.py       # Fichier d'initialisation du package config
│   │   └── settings.py       # Paramètres de configuration (fuseau horaire, logging)
│   └── .env                  # Fichier de configuration des variables d’environnement
├── client/
│   ├── __init__.py           # Fichier d'initialisation du package client
│   └── client_rest.py        # Client REST pour tests automatisés
├── test/
│   ├── __init__.py           # Fichier d'initialisation du package test
│   └── test_client_rest.py   # Tests automatisés (unitaires + intégration) pour client REST
├── README.md                 # Documentation principale du projet
├── start_jsonflow.bat        # Script de démarrage Windows
└── start_jsonflow.sh         # Script de démarrage Linux/macOS
```

## 💡 Exemple d'utilisation

Voici comment envoyer une commande de mouvement au robot :

1. Envoyez une requête POST à l'endpoint /command avec le body suivant :

```json
{
  "command": "move",
  "direction": "forward",
  "speed": 0.7,
  "duration": 3
}
```

2. L'API retournera la commande validée avec le message :

```json
{
  "message": "✅ Commande validée",
  "data": {
    "command": "move",
    "direction": "forward",
    "speed": 0.7,
    "duration": 3,
    "timestamp": "2025-11-08T10:30:00+00:00",
    "tz": "UTC",
    "mode": "manual"
  }
}
```

## 🔒 Validation des Commandes

Les commandes envoyées à l'API sont validées selon des règles métier spécifiques :

| Type de commande | Règles de validation |
|------------------|----------------------|
| **move** | `direction` et `speed` obligatoires ; `duration ≤ 10s` ; en mode `auto`, `speed ≤ 0.5`. |
| **sensor** | `sensor_type` obligatoire. |

## 🌐 Configuration du Fuseau Horaire

- Le fuseau horaire par défaut est défini dans le fichier `.env`.

Exemple :

```env
# Fichier .env
DEFAULT_TZ=Europe/Paris
```
