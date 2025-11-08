#!/bin/bash

# Fonction pour afficher des messages de statut
function status_message {
    echo -e "\033[1;32m$1\033[0m"
}

# Fonction pour afficher des messages d'erreur
function error_message {
    echo -e "\033[1;31m$1\033[0m"
}

# ==========================================================
# Vérifie la présence de Python
# ==========================================================
status_message "Vérification de Python..."

if ! command -v python3 &> /dev/null; then
    error_message "❌ Python n'est pas installé ou non trouvé dans le PATH."
    echo "Installez Python 3.10+ avant d'exécuter ce script."
    exit 1
fi

# ==========================================================
# Vérifie si l'environnement virtuel existe
# ==========================================================
if [ ! -d ".venv" ]; then
    status_message "🔧 Création de l'environnement virtuel..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        error_message "❌ Erreur lors de la création du venv."
        exit 1
    fi

    status_message "📦 Installation des dépendances..."
    source .venv/bin/activate
    python3 -m pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
else
    status_message "✅ Environnement virtuel détecté."
fi

# ==========================================================
# Active l'environnement virtuel
# ==========================================================
status_message "🟢 Activation de l'environnement virtuel..."
source .venv/bin/activate

# ==========================================================
# Démarre le serveur FastAPI dans une nouvelle fenêtre de terminal
# ==========================================================
status_message "🚀 Démarrage du serveur FastAPI..."
gnome-terminal -- bash -c "source .venv/bin/activate && uvicorn jsonFlow_api.main:app --reload; exec bash"

# ==========================================================
# Attente que le serveur soit prêt
# ==========================================================
status_message "🕒 Vérification que le serveur répond avant exécution du client et génération du README_JSONFLOW..."

RETRIES=15
COUNT=0
SERVER_READY=false

while [ $COUNT -lt $RETRIES ]; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/arkdown-docs)

    if [ "$STATUS" == "200" ]; then
        status_message "✅ Serveur prêt !"
        SERVER_READY=true
        break
    fi

    COUNT=$((COUNT + 1))
    sleep 1
done

if [ "$SERVER_READY" = false ]; then
    error_message "⚠️ Le serveur n'a pas répondu à temps. Client et README_JSONFLOW.md non exécutés."
    exit 1
fi

# ==========================================================
# Démarre le client REST dans une autre fenêtre de terminal
# ==========================================================
if [ -f "client/client_rest.py" ]; then
    status_message "🧪 Exécution du client REST..."
    gnome-terminal -- bash -c "source .venv/bin/activate && python3 client/client_rest.py; exec bash"
else
    error_message "⚠️ Aucun client REST trouvé dans client/client_rest.py"
fi

# ==========================================================
# Affichage du statut final
# ==========================================================
status_message "✅ API JsonFlow en cours d’exécution sur http://127.0.0.1:8000"