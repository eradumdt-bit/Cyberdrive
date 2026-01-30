# 🚗 CyberDrive - Version Web

Version web de CyberDrive permettant le contrôle à distance via navigateur.

## 📐 Architecture

```
┌──────────────────────┐         ┌───────────────────────┐         ┌──────────────┐
│   NAVIGATEUR WEB     │◄───────►│  SERVEUR PROXMOX      │◄───────►│  PC LOCAL    │
│  (De partout)        │  HTTPS  │  main_server.py       │  WebSocket│ web_client.py│
│  Dashboard HTML      │         │  Interface Web        │         │  USB→ESP32   │
└──────────────────────┘         └───────────────────────┘         └──────┬───────┘
                                                                            │
                                                                          USB
                                                                            │
                                                                       ┌────▼────┐
                                                                       │  ESP32  │
                                                                       └────┬────┘
                                                                         Sans fil
                                                                            │
                                                                       ┌────▼──────┐
                                                                       │Arduino Mega│
                                                                       │  Voiture   │
                                                                       └───────────┘
```

## ⚡ Installation Rapide

### 1️⃣ Sur le SERVEUR PROXMOX

```bash
# Créer un container LXC Ubuntu 24.04 dans Proxmox UI
# puis entrer dedans :
pct enter [ID_CONTAINER]

# Installation
apt update && apt install python3 python3-pip git -y

# Récupérer les fichiers
cd /opt
# Option A: Upload manuel des fichiers
# Option B: Git clone si tu les push sur GitHub

# Installer les dépendances
cd cyberdrive_web
pip3 install -r requirements.txt --break-system-packages

# Lancer le serveur
python3 main_server.py
```

Le serveur sera accessible sur : **http://IP_DU_CONTAINER:5000**

### 2️⃣ Sur ton PC LOCAL (Windows)

```bash
# Installer Python 3.11+ si pas déjà fait
# https://www.python.org/downloads/

# Dans un dossier de ton choix
cd C:\CyberDrive
# Copier web_client.py et requirements.txt ici

# Installer les dépendances
pip install -r requirements.txt

# IMPORTANT: Éditer web_client.py ligne 15
# Remplacer par l'IP de ton serveur Proxmox :
# SERVER_URL = 'http://192.168.1.100:5000'

# Brancher l'ESP32 en USB puis lancer
python web_client.py
```

### 3️⃣ Accéder au Dashboard

Ouvre un navigateur et va sur : **http://IP_SERVEUR_PROXMOX:5000**

Tu verras :
- ✅ Serveur : online
- ✅ Client USB : online (quand web_client.py tourne)
- ✅ Véhicule : online (quand ESP32 est connecté)

## 🎮 Utilisation

### Dashboard Web

Le dashboard affiche :

1. **📊 Télémétrie en temps réel**
   - Direction (PWM 1000-2000 µs)
   - Accélération (PWM 1000-2000 µs)
   - Distance (capteur ultrason en cm)
   - Batterie (voltage)
   - Signal RC (actif/inactif)
   - Mode (manual/auto)

2. **🎮 Contrôles**
   - ⬆️ Avant
   - ⬇️ Arrière
   - ⬅️ Gauche
   - ➡️ Droite
   - 🛑 Stop

3. **📷 Caméra** (si activée)

4. **📈 Statistiques**
   - Commandes envoyées
   - Télémétrie reçue
   - Uptime serveur

5. **📝 Logs** en temps réel

### Format de Communication

#### ESP32 → Serveur (Télémétrie)
```
TELEM:{direction}:{throttle}:{distance}:{battery}:{rx_active}
Exemple: TELEM:1500:1520:45:11.8:1
```

#### Serveur → ESP32 (Commande)
```
CMD:MOVE:{direction}:{throttle}
Exemple: CMD:MOVE:1700:1600
```

## 🌐 Accès depuis Internet

### Option A: Port Forwarding

1. **Sur ton routeur:**
   - Forward port `5000` → IP du container Proxmox
   - Exemple: `INTERNET:5000 → 192.168.1.100:5000`

2. **Accès:**
   - Trouve ton IP publique: https://whatismyip.com
   - Accès: `http://TON_IP_PUBLIQUE:5000`

⚠️ **ATTENTION:** HTTP n'est PAS sécurisé. Ajoute HTTPS (voir ci-dessous).

### Option B: Cloudflare Tunnel (RECOMMANDÉ)

Gratuit, sécurisé, pas besoin d'ouvrir de ports !

```bash
# Dans le container Proxmox
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
dpkg -i cloudflared.deb

# Authentification
cloudflared tunnel login

# Créer tunnel
cloudflared tunnel create cyberdrive

# Configurer
nano ~/.cloudflared/config.yml
```

Contenu de `config.yml`:
```yaml
tunnel: [ID_GENERE]
credentials-file: /root/.cloudflared/[ID].json

ingress:
  - hostname: cyberdrive.ton-domaine.com
    service: http://localhost:5000
  - service: http_status:404
```

```bash
# Lancer
cloudflared tunnel run cyberdrive

# Auto-start
cloudflared service install
```

Ton site: `https://cyberdrive.ton-domaine.com` 🎉

### Option C: Tailscale (VPN Simple)

```bash
# Sur Proxmox ET sur ton PC
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

# Accès direct via IP Tailscale (100.x.x.x)
```

## 🔒 Sécuriser (Production)

### HTTPS avec Nginx + Let's Encrypt

```bash
apt install nginx certbot python3-certbot-nginx -y

# Config Nginx
nano /etc/nginx/sites-available/cyberdrive
```

```nginx
server {
    listen 80;
    server_name ton-domaine.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/cyberdrive /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# SSL gratuit
certbot --nginx -d ton-domaine.com
```

### Démarrage Automatique (systemd)

```bash
nano /etc/systemd/system/cyberdrive.service
```

```ini
[Unit]
Description=CyberDrive Web Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cyberdrive_web
ExecStart=/usr/bin/python3 /opt/cyberdrive_web/main_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable cyberdrive
systemctl start cyberdrive
systemctl status cyberdrive
```

## 🛠️ Configuration

### Ajouter un Véhicule

Créer un fichier JSON dans `config/vehicles/`:

```json
{
  "id": "mon_vehicule",
  "name": "Ma Voiture RC",
  "type": "rc_car",
  "description": "Description",
  
  "connection": {
    "preferred_mode": "serial",
    "serial": {
      "port": "AUTO",
      "baudrate": 115200
    }
  },
  
  "limits": {
    "dir_min": 1000,
    "dir_max": 2000,
    "dir_center": 1500,
    "thr_min": 1000,
    "thr_max": 2000,
    "thr_neutral": 1500
  }
}
```

### Changer le Port du Serveur

Dans `main_server.py` ligne ~357:
```python
socketio.run(app, host='0.0.0.0', port=8080)  # Au lieu de 5000
```

### Changer l'URL du Serveur (Client USB)

Dans `web_client.py` ligne 15:
```python
SERVER_URL = 'http://mon-serveur.com:5000'
```

Ou en ligne de commande:
```bash
python web_client.py http://mon-serveur.com:5000
```

## 🐛 Dépannage

### Serveur ne démarre pas

```bash
# Vérifier les logs
journalctl -u cyberdrive -f

# Tester manuellement
python3 main_server.py

# Vérifier le port
netstat -tlnp | grep 5000
```

### Client USB ne trouve pas l'ESP32

```bash
# Sur Windows
python -m serial.tools.list_ports

# Installer drivers si besoin:
# - CH340: https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers
# - CP2102: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
```

### "Connection refused"

- ✅ Serveur tourne ? `systemctl status cyberdrive`
- ✅ Firewall ? `ufw allow 5000`
- ✅ IP correcte dans web_client.py ?
- ✅ Ping le serveur depuis ton PC

### WebSocket ne se connecte pas

- ✅ Teste l'API REST: `http://IP:5000/api/status`
- ✅ Regarde les logs du serveur
- ✅ Vérifie CORS si domaine différent

### Télémétrie ne s'affiche pas

- ✅ Client USB connecté ? (voyant vert)
- ✅ ESP32 envoie bien "TELEM:..." ?
- ✅ Regarde les logs web_client.py

## 📊 Différences avec main.py Original

| Aspect | main.py (Original) | main_server.py (Web) |
|--------|-------------------|---------------------|
| Interface | PyQt6 Desktop | HTML/JS Web |
| Connexion ESP32 | Direct USB | Via web_client.py |
| Accessibilité | PC local seulement | De partout (Internet) |
| Multi-utilisateurs | Non | Oui |
| Déploiement | Exe Windows | Serveur Linux |

## 📝 TODO / Améliorations Futures

- [ ] Authentification (login/password)
- [ ] Support caméra vidéo temps réel
- [ ] Enregistrement des sessions
- [ ] Mode automatique (autopilot)
- [ ] Support de plusieurs véhicules simultanés
- [ ] Application mobile (React Native)
- [ ] Graphiques de télémétrie historique
- [ ] Export des données (CSV, JSON)

## 🆘 Support

- Issues GitHub: [ton-repo]/issues
- Documentation: README.md
- Logs serveur: `journalctl -u cyberdrive -f`
- Logs client: Dans la console Python

## 📜 Licence

Même licence que le projet original CyberDrive.

---

**Version:** 0.1 Alpha  
**Auteur:** eradumdt-bit  
**Date:** Janvier 2026
