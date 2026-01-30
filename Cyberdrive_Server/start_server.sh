#!/bin/bash
# Script de lancement rapide du serveur CyberDrive

echo "=========================================="
echo "  CyberDrive Web Server - Start Script"
echo "=========================================="
echo ""

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé!"
    echo "Installation: apt install python3 python3-pip"
    exit 1
fi

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 n'est pas installé!"
    echo "Installation: apt install python3-pip"
    exit 1
fi

# Vérifier si les dépendances sont installées
echo "🔍 Vérification des dépendances..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "📦 Installation des dépendances..."
    pip3 install -r requirements.txt --break-system-packages
else
    echo "✅ Dépendances OK"
fi

# Vérifier les dossiers
if [ ! -d "config/vehicles" ]; then
    echo "📁 Création du dossier config/vehicles..."
    mkdir -p config/vehicles
fi

if [ ! -d "templates" ]; then
    echo "❌ Erreur: Dossier templates/ manquant!"
    exit 1
fi

# Obtenir l'IP locale
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "✅ Prêt à démarrer!"
echo ""
echo "  Accès local:    http://localhost:5000"
echo "  Accès réseau:   http://$IP:5000"
echo ""
echo "  API Status:     http://$IP:5000/api/status"
echo "  Véhicules:      http://$IP:5000/api/vehicles"
echo ""
echo "=========================================="
echo ""
echo "Appuie sur Ctrl+C pour arrêter le serveur"
echo ""

# Lancer le serveur
python3 main_server.py
