# 🚀 Guide de Démarrage Rapide

## ⚡ Installation Express (5 minutes)

### SUR LE SERVEUR PROXMOX

```bash
# 1. Créer un container LXC Ubuntu 24.04 dans Proxmox
#    (1 CPU, 512MB RAM, 4GB disk)

# 2. Entrer dans le container
pct enter [ID]

# 3. Installation rapide
apt update && apt install python3 python3-pip unzip -y

# 4. Upload et extraction (choisir une méthode)

## Méthode A: Via WinSCP / scp
# Upload le dossier cyberdrive_web vers /opt/

## Méthode B: Via wget (si sur GitHub)
# cd /opt
# wget https://github.com/TON_USER/cyberdrive/archive/refs/heads/main.zip
# unzip main.zip

# 5. Lancer
cd /opt/cyberdrive_web
chmod +x start_server.sh
./start_server.sh
```

### SUR TON PC WINDOWS

```bash
# 1. Installer Python 3.11+
#    https://www.python.org/downloads/
#    ⚠️ Cocher "Add Python to PATH"

# 2. Créer un dossier
mkdir C:\CyberDrive
cd C:\CyberDrive

# 3. Copier web_client.py et requirements.txt

# 4. Éditer web_client.py
#    Ligne 15: SERVER_URL = 'http://IP_DE_TON_PROXMOX:5000'

# 5. Installer dépendances
pip install -r requirements.txt

# 6. Brancher ESP32 en USB

# 7. Lancer
python web_client.py
```

### DANS TON NAVIGATEUR

```
http://IP_DE_TON_PROXMOX:5000
```

## ✅ Vérification

Tu devrais voir:
- 🟢 Serveur: online
- 🟢 Client USB: online
- 🟢 Véhicule: online

Si un voyant est rouge, consulte le README section Dépannage.

## 🎮 Utiliser

1. Clique sur les boutons (Avant, Arrière, etc.)
2. Regarde la télémétrie en temps réel
3. Les commandes sont envoyées: PC → Serveur Proxmox → PC USB → ESP32 → Arduino

## 🌐 Accéder depuis Internet

Voir README.md section "Accès depuis Internet" pour:
- Port forwarding
- Cloudflare Tunnel (recommandé)
- Tailscale VPN

## 📞 Besoin d'aide ?

1. Lis le README.md complet
2. Vérifie les logs:
   - Serveur: `journalctl -u cyberdrive -f` (si service)
   - Serveur: Dans la console si lancé manuellement
   - Client: Dans la console Python
3. Teste l'API: `http://IP:5000/api/status`

---

**Bon voyage avec CyberDrive ! 🚗💨**
