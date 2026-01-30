# 🚗 CyberDrive Web - Projet Complet

## 📦 Contenu du Package

```
cyberdrive_web/
├── main_server.py          # Serveur principal (Proxmox)
├── web_client.py           # Client USB (PC local avec ESP32)
├── templates/
│   └── index.html          # Interface web dashboard
├── config/
│   └── vehicles/
│       └── car_001.json    # Configuration véhicule exemple
├── requirements.txt        # Dépendances Python
├── start_server.sh         # Script de lancement serveur
├── README.md               # Documentation complète
└── QUICKSTART.md           # Guide démarrage rapide
```

## 🎯 Ce que tu as maintenant

### ✅ Version Web Complète de ton main.py

**Serveur (main_server.py)**
- ✅ Remplace l'UI PyQt par une interface web
- ✅ Gère toute la logique métier de ton main.py original
- ✅ Communication WebSocket temps réel
- ✅ API REST pour stats et infos
- ✅ Support multi-clients (plusieurs navigateurs)
- ✅ Accessible de partout avec une IP/domaine

**Client USB (web_client.py)**
- ✅ Se connecte à l'ESP32 via USB (comme ton main.py)
- ✅ Lit la télémétrie du port série
- ✅ Envoie les commandes au véhicule
- ✅ Relaie tout au serveur Proxmox via WebSocket
- ✅ Auto-détection de l'ESP32
- ✅ Reconnexion automatique

**Interface Web (index.html)**
- ✅ Dashboard moderne et responsive
- ✅ Télémétrie temps réel
- ✅ Contrôles de direction (avant/arrière/gauche/droite/stop)
- ✅ Affichage caméra (prêt pour l'avenir)
- ✅ Statistiques et logs
- ✅ Indicateurs de status (serveur/USB/véhicule)

## 🏗️ Architecture Complète

```
                    INTERNET
                       ↕
        ┌──────────────────────────┐
        │    SERVEUR PROXMOX       │
        │  (Container LXC Ubuntu)  │
        │                          │
        │   main_server.py         │
        │   ├── Flask Web Server   │
        │   ├── SocketIO WebSocket │
        │   ├── API REST           │
        │   └── templates/         │
        │       └── index.html     │
        └──────────────┬───────────┘
                       ↕ WebSocket
        ┌──────────────────────────┐
        │      PC LOCAL            │
        │    (Windows/Linux)       │
        │                          │
        │   web_client.py          │
        │   ├── Serial Reader      │
        │   ├── SocketIO Client    │
        │   └── Command Relay      │
        └──────────────┬───────────┘
                       ↕ USB
              ┌────────────────┐
              │     ESP32      │
              └────────┬───────┘
                       ↕ Sans fil
              ┌────────────────┐
              │  Arduino Mega  │
              │   Voiture RC   │
              └────────────────┘
```

## 🚀 Prochaines Étapes

### 1. Installation Serveur (Proxmox)

```bash
# Voir QUICKSTART.md ou README.md
./start_server.sh
```

### 2. Installation Client (PC)

```bash
# Éditer web_client.py ligne 15 avec l'IP du serveur
python web_client.py
```

### 3. Accès Dashboard

```
http://IP_SERVEUR:5000
```

## 🎨 Fonctionnalités

### Implémentées ✅
- [x] Communication WebSocket bidirectionnelle
- [x] Télémétrie temps réel
- [x] Contrôles manuels (clavier virtuel)
- [x] Multi-clients web
- [x] Auto-reconnexion
- [x] Support USB série
- [x] Config véhicules JSON
- [x] Logs système
- [x] Statistiques
- [x] Status indicators

### Futures 🔮
- [ ] Caméra vidéo streaming
- [ ] Mode automatique
- [ ] Authentification utilisateur
- [ ] Enregistrement sessions
- [ ] Graphiques historiques
- [ ] Multi-véhicules simultanés
- [ ] App mobile
- [ ] Gamepad/Joystick support

## 📋 Compatibilité

### Serveur
- ✅ Ubuntu 24.04 (LXC Container)
- ✅ Debian 12+
- ✅ Raspberry Pi OS
- ✅ Tout Linux moderne

### Client USB
- ✅ Windows 10/11
- ✅ Linux
- ✅ macOS

### Navigateurs
- ✅ Chrome/Edge (recommandé)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile (iOS/Android)

## 🔧 Configuration

### Changer l'IP du serveur

**Dans web_client.py:**
```python
SERVER_URL = 'http://TON_IP:5000'  # Ligne 15
```

### Changer le port

**Dans main_server.py:**
```python
socketio.run(app, host='0.0.0.0', port=8080)  # Ligne ~357
```

### Ajouter un véhicule

Créer `config/vehicles/nouveau.json`:
```json
{
  "id": "mon_vehicule",
  "name": "Ma Voiture",
  "connection": {
    "preferred_mode": "serial",
    "serial": {
      "port": "AUTO",
      "baudrate": 115200
    }
  }
}
```

## 🌐 Accès Internet

### 3 Options Principales:

**A. Port Forwarding** (Simple mais HTTP)
- Forward 5000 → IP container
- Accès: `http://IP_PUBLIQUE:5000`

**B. Cloudflare Tunnel** (Recommandé - HTTPS gratuit)
- Pas d'ouverture de ports
- HTTPS automatique
- Protection DDoS
- Accès: `https://cyberdrive.ton-domaine.com`

**C. Tailscale VPN** (Réseau privé)
- VPN P2P
- Sécurisé par défaut
- Accès: `http://100.x.x.x:5000`

Voir README.md pour les guides détaillés.

## 🐛 Besoin d'Aide ?

1. **Lis d'abord:**
   - QUICKSTART.md (démarrage rapide)
   - README.md (guide complet)

2. **Vérifie:**
   - Serveur tourne ? `ps aux | grep main_server`
   - Client USB connecté ? (voyant vert)
   - ESP32 branché ? `python -m serial.tools.list_ports`

3. **Logs:**
   - Serveur: console ou `journalctl -u cyberdrive -f`
   - Client: console Python
   - API: `curl http://IP:5000/api/status`

4. **Test API:**
```bash
# Status
curl http://IP:5000/api/status

# Véhicules
curl http://IP:5000/api/vehicles

# Télémétrie
curl http://IP:5000/api/telemetry
```

## 📊 Comparaison avec Original

| Feature | main.py (Original) | CyberDrive Web |
|---------|-------------------|----------------|
| Interface | PyQt6 Desktop | Web HTML/JS |
| ESP32 | Direct USB | Via web_client.py |
| Accessibilité | Local seulement | Internet |
| Multi-users | Non | Oui |
| Mobile | Non | Oui (navigateur) |
| Déploiement | .exe Windows | Serveur Linux |
| Auto-start | Non | systemd |

## 🎓 Code Structure

**main_server.py** (serveur)
- Flask app configuration
- WebSocket events handlers
- API REST routes
- State management
- Vehicle configuration loader

**web_client.py** (client USB)
- Serial port management
- ESP32 auto-detection
- Telemetry parser
- WebSocket client
- Command relay

**index.html** (interface)
- Dashboard UI
- Real-time updates
- WebSocket client
- Control buttons
- Telemetry display

## 📄 Licence

Projet open-source.
Même licence que CyberDrive original.

## 👤 Crédits

- **Projet Original:** eradumdt-bit/Cyberdrive
- **Version Web:** Adaptation pour déploiement Proxmox
- **Date:** Janvier 2026
- **Version:** 0.1 Alpha

---

**Prêt à rouler ! 🚗💨**

Pour commencer, ouvre QUICKSTART.md
