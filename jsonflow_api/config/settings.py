# jsonflow_api/settings.py

"""
Configuration centrale de l'application JsonFlow.

Ce module gère :
- le chargement des variables d'environnement,
- la configuration du fuseau horaire par défaut,
- la configuration du logging global.
"""

import os
import zoneinfo
import logging
from dotenv import load_dotenv

# =========================
# --- VARIABLES D'ENVIRONNEMENT
# =========================

# Chargement des variables depuis le fichier .env à la racine du projet
load_dotenv()

# Fuseau horaire par défaut si non spécifié dans les variables d'environnement
DEFAULT_TZ = os.getenv("DEFAULT_TZ", "UTC")

# =========================
# --- CONFIGURATION DU LOGGING
# =========================

# Logging global pour toute l'application
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.info(f"Fuseau horaire par défaut : {DEFAULT_TZ}")

# =========================
# --- GESTION DU FUSEAU HORAIRE
# =========================

# Création d'un objet ZoneInfo centralisé pour le fuseau horaire
try:
    DEFAULT_TZINFO = zoneinfo.ZoneInfo(DEFAULT_TZ)
except zoneinfo.ZoneInfoNotFoundError:
    raise ValueError(f"Fuseau horaire invalide spécifié : {DEFAULT_TZ}")