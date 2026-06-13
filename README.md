# Whisper Dictation

Free Windows 11 push-to-talk voice dictation using local Whisper AI — no subscriptions, no cloud, no Windows Speech Recognition.

---

## English

### Requirements
- Windows 11 x64
- Python 3.11 or newer (download from python.org)
- A working microphone

### Installation

```powershell
# 1 — Clone the repository
git clone https://github.com/YOUR_USER/whisper-dictation.git
cd whisper-dictation

# 2 — Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# 3 — Install dependencies
pip install -r requirements.txt

# 4 — Install the package in editable mode
pip install -e .
```

### Usage

```powershell
# From inside the virtual environment:
python -m whisper_dictation
```

A small **white circle** appears in the system tray.

| Action | Result |
|---|---|
| **Hold** Right Ctrl | Red circle appears — microphone is recording |
| **Release** Right Ctrl | Transcription runs locally; text is pasted into the focused window |
| **Right-click tray** → Settings | Opens `config.yaml` in Notepad |
| **Right-click tray** → Quit | Exits the app |

> **First run:** The Whisper model (~150 MB for `base`) is downloaded automatically to  
> `%APPDATA%\whisper-dictation\models\` and cached for all future uses.

### Configuration

The config file is created automatically at `%APPDATA%\whisper-dictation\config.yaml` on first run.

```yaml
hotkey: "right ctrl"   # Key to hold while speaking
model: "base"          # tiny | base | small | medium | large-v3
language: "fr"         # ISO 639-1 code, or null for auto-detect
```

After editing, **restart the app** for changes to take effect.

### Packaging as a single .exe

```powershell
pip install pyinstaller==6.11.1
pyinstaller whisper_dictation.spec
# Output: dist\whisper-dictation.exe
```

---

## Français

### Prérequis
- Windows 11 x64
- Python 3.11 ou plus récent (téléchargeable sur python.org)
- Un microphone fonctionnel

### Installation

```powershell
# 1 — Cloner le dépôt
git clone https://github.com/VOTRE_USER/whisper-dictation.git
cd whisper-dictation

# 2 — Créer et activer un environnement virtuel (recommandé)
python -m venv .venv
.venv\Scripts\activate

# 3 — Installer les dépendances
pip install -r requirements.txt

# 4 — Installer le paquet en mode éditable
pip install -e .
```

### Utilisation

```powershell
python -m whisper_dictation
```

Une petite **icône blanche** apparaît dans la barre des tâches (zone de notification).

| Action | Résultat |
|---|---|
| **Maintenir** Ctrl droit | Icône rouge — le microphone enregistre |
| **Relâcher** Ctrl droit | Transcription locale ; le texte est collé dans la fenêtre active |
| **Clic droit** → Paramètres | Ouvre `config.yaml` dans le Bloc-notes |
| **Clic droit** → Quitter | Ferme l'application |

> **Premier démarrage :** Le modèle Whisper (~150 Mo pour `base`) est téléchargé automatiquement dans  
> `%APPDATA%\whisper-dictation\models\` et mis en cache pour les utilisations suivantes.

### Configuration

Le fichier de configuration est créé automatiquement dans `%APPDATA%\whisper-dictation\config.yaml` au premier lancement.

```yaml
hotkey: "right ctrl"   # Touche à maintenir pendant la dictée
model: "base"          # tiny | base | small | medium | large-v3
language: "fr"         # Code ISO 639-1, ou null pour détection automatique
```

Redémarrez l'application après toute modification.

### Créer un exécutable .exe autonome

```powershell
pip install pyinstaller==6.11.1
pyinstaller whisper_dictation.spec
# Résultat : dist\whisper-dictation.exe
```

---

## License

MIT
