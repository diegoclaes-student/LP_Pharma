# Configuration Google Sheets — Guide de Setup

Ce guide explique comment configurer l'accès à Google Sheets pour le scraper LP_Pharma.

---

## Prérequis

- Un compte Google
- Accès à Google Cloud Console
- La Google Sheet cible (`test_pharma_scrap`) créée

---

## Étape 1 : Créer un projet Google Cloud

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Cliquer sur **Select a project** → **New Project**
3. Nom du projet : `lp-pharma-scraper` (ou au choix)
4. Cliquer sur **Create**

---

## Étape 2 : Activer l'API Google Sheets

1. Dans le projet créé, aller à **APIs & Services** → **Library**
2. Rechercher "Google Sheets API"
3. Cliquer sur **Google Sheets API**
4. Cliquer sur **Enable**

---

## Étape 3 : Créer un Service Account

1. Aller à **APIs & Services** → **Credentials**
2. Cliquer sur **Create Credentials** → **Service Account**
3. Remplir les informations :
   - **Service account name** : `lp-pharma-scraper-sa`
   - **Service account ID** : (généré automatiquement)
   - **Description** : `Service account for LP_Pharma scraper`
4. Cliquer sur **Create and Continue**
5. **Grant this service account access to project** : laisser vide, cliquer **Continue**
6. **Grant users access to this service account** : laisser vide, cliquer **Done**

---

## Étape 4 : Générer la clé JSON

1. Dans la liste des **Service Accounts**, cliquer sur le SA créé (`lp-pharma-scraper-sa@...`)
2. Aller dans l'onglet **Keys**
3. Cliquer sur **Add Key** → **Create new key**
4. Choisir **JSON**
5. Cliquer sur **Create**
6. Le fichier JSON se télécharge automatiquement (ex: `lp-pharma-scraper-sa-abc123.json`)

⚠️ **Important** : ce fichier contient des credentials sensibles. Ne le partagez jamais et ne le commitez pas dans Git.

---

## Étape 5 : Placer la clé sur votre machine

### Option A : Emplacement recommandé (par défaut)

```bash
mkdir -p ~/.config/lp_pharma
mv ~/Downloads/lp-pharma-scraper-sa-*.json ~/.config/lp_pharma/sa_key.json
chmod 600 ~/.config/lp_pharma/sa_key.json
```

### Option B : Variable d'environnement

Si vous placez la clé ailleurs, définissez la variable :

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/chemin/vers/votre/sa_key.json"
```

Pour la rendre permanente, ajoutez dans `~/.zshrc` ou `~/.bashrc` :

```bash
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/lp_pharma/sa_key.json"' >> ~/.zshrc
source ~/.zshrc
```

---

## Étape 6 : Partager la Google Sheet avec le Service Account

1. Ouvrir votre fichier JSON et copier l'adresse email du service account :
   ```json
   {
     "client_email": "lp-pharma-scraper-sa@PROJECT-ID.iam.gserviceaccount.com",
     ...
   }
   ```

2. Ouvrir la Google Sheet `test_pharma_scrap` dans votre navigateur

3. Cliquer sur **Partager** (bouton en haut à droite)

4. Coller l'email du service account : `lp-pharma-scraper-sa@PROJECT-ID.iam.gserviceaccount.com`

5. Définir les permissions : **Éditeur** (Editor)

6. Décocher "Notify people" (pas besoin de notifier un service account)

7. Cliquer sur **Partager** ou **Send**

✅ Le service account a maintenant accès à la feuille

---

## Étape 7 : Installer les dépendances Python

```bash
cd /Users/diegoclaes/Code/LP_Pharma
conda activate scraping
pip install -r requirements.txt
```

Cela installera :
- `gspread` (client Google Sheets)
- `google-auth` (authentification)
- `google-auth-oauthlib` (OAuth)
- `google-auth-httplib2` (transport HTTP)

---

## Étape 8 : Tester la connexion

### Test simple avec Python

```bash
conda activate scraping
python -c "
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds_path = Path.home() / '.config' / 'lp_pharma' / 'sa_key.json'
creds = Credentials.from_service_account_file(
    str(creds_path),
    scopes=SCOPES
)
client = gspread.authorize(creds)
sheet = client.open('test_pharma_scrap')
print(f'✅ Connexion réussie: {sheet.url}')
"
```

Si vous voyez `✅ Connexion réussie`, tout est OK !

### Test avec le module google_sheets

```bash
conda activate scraping
cd /Users/diegoclaes/Code/LP_Pharma
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))

from google_sheets import open_sheet
sheet = open_sheet('test_pharma_scrap')
print(f'✅ Sheet ouverte: {sheet.title}')
"
```

---

## Étape 9 : Préparer la Google Sheet

Votre feuille `test_pharma_scrap` doit avoir un onglet `resultats_final` avec au minimum ces colonnes (ligne 1) :

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| Nom_Produit | **CNK** | Prix_Base | Prix_MediMarket | Prix_Multipharma | Prix_NewPharma | Match_Multipharma | Match_Source_Multipharma | Prix Moyen | Prix Min |

La colonne **CNK** (colonne B) doit contenir les codes CNK à scraper.

Exemple :

| Nom_Produit | CNK | Prix_Base | Prix_MediMarket | Prix_Multipharma | ... |
|-------------|-----|-----------|-----------------|------------------|-----|
| Caudalie Gel Douche | 4487039 | 12 | | | |
| Caudalie Crème | 4886552 | 14,1 | | | |

Les colonnes de prix seront remplies automatiquement par le scraper.

---

## Étape 10 : Lancer le scraper en mode Sheet

```bash
conda activate scraping
cd /Users/diegoclaes/Code/LP_Pharma

# Lancer le scraping depuis Google Sheets
python src/scraper.py --sheet test_pharma_scrap
```

Le scraper va :
1. Lire les CNK depuis la colonne B de l'onglet `resultats_final`
2. Scraper les prix sur Medi-Market et Multipharma
3. Calculer Prix Moyen et Prix Min
4. Écrire tous les résultats dans la feuille en batch

---

## Dépannage

### Erreur : "Spreadsheet not found"

→ Vérifiez que :
- Le nom de la sheet est correct (`test_pharma_scrap`)
- La sheet est partagée avec le service account email
- Le service account a les permissions "Éditeur"

### Erreur : "Credentials file not found"

→ Vérifiez que :
- Le fichier JSON existe dans `~/.config/lp_pharma/sa_key.json`
- Ou que `GOOGLE_APPLICATION_CREDENTIALS` est défini correctement

### Erreur : "Column 'CNK' not found"

→ Vérifiez que :
- L'onglet `resultats_final` existe
- La ligne 1 contient un header "CNK" (colonne B)

### Erreur : "Invalid grant" ou "Token expired"

→ Régénérez une nouvelle clé JSON :
1. Supprimer l'ancienne clé dans Google Cloud Console
2. Créer une nouvelle clé (étape 4)
3. Remplacer le fichier JSON local

---

## Sécurité

✅ **À faire** :
- Stocker le fichier JSON hors du dépôt Git
- Définir `chmod 600` sur le fichier JSON
- Limiter l'accès au service account (seulement la sheet cible)

❌ **À ne pas faire** :
- Committer le fichier JSON dans Git
- Partager le fichier JSON publiquement
- Utiliser le même SA pour plusieurs projets non liés

---

## Références

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [gspread Documentation](https://docs.gspread.org/)
- [Service Accounts Guide](https://cloud.google.com/iam/docs/service-accounts)

---

✅ Configuration terminée ! Vous pouvez maintenant utiliser le scraper en mode Google Sheets.
