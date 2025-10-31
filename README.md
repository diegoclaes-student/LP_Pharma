# 🏥 LP_Pharma - Comparateur de Prix Pharmaceutiques

Outil automatisé pour scraper et comparer les prix de produits pharmaceutiques sur les sites belges.

---

## 🚀 Démarrage Rapide

### Installation

```bash
# Installer les dépendances
./install.sh

# Activer l'environnement
conda activate scraping
```

### Mode 1 : Fichier CSV

#### 1. Préparer votre fichier d'entrée

Créez un fichier CSV dans `data/input/` avec le format suivant (séparateur: `;`):

```csv
name;CNK;prix
Caudalie Gel Douche;4487039;12
Caudalie Crème Mains;4886552;14,1
```

#### 2. Lancer le scraper

```bash
./run_scraper.sh data/input/votre_fichier.csv data/output/resultats.csv
```

**Ou avec les valeurs par défaut:**

```bash
./run_scraper.sh
```

#### 3. Consulter les résultats

Les résultats seront dans `data/output/` avec horodatage automatique.

### Mode 2 : Google Sheets 🆕

#### 1. Configuration (une seule fois)

Suivez le guide complet : [`docs/GS_SETUP.md`](docs/GS_SETUP.md)

Résumé :
1. Créer un Service Account dans Google Cloud Console
2. Activer l'API Google Sheets
3. Télécharger la clé JSON et la placer dans `~/.config/lp_pharma/sa_key.json`
4. Partager votre Google Sheet avec le service account email

#### 2. Préparer votre Google Sheet

Créez une feuille nommée `test_pharma_scrap` avec un onglet `resultats_final` contenant :

| Nom_Produit | CNK | Prix_Base | Prix_MediMarket | Prix_Multipharma | Prix_NewPharma | Match_Multipharma | Match_Source_Multipharma | Prix Moyen | Prix Min |
|-------------|-----|-----------|-----------------|------------------|----------------|-------------------|--------------------------|------------|----------|
| Produit 1 | 4487039 | 12 | | | | | | | |
| Produit 2 | 4886552 | 14,1 | | | | | | | |

#### 3. Lancer le scraper

```bash
conda activate scraping
python src/scraper.py --sheet test_pharma_scrap
```
Bonne commande
/opt/miniconda3/envs/scraping/bin/python src/scraper.py --sheet test_pharma_scrap --creds /Users/diegoclaes/Code/LP_Pharma/sa_key.json

Le scraper lira les CNK depuis la colonne B et écrira les résultats directement dans la feuille !

---

## 📂 Structure du Projet

```
LP_Pharma/
├── 🚀 run_scraper.sh              # Script de lancement
├── 📄 README.md                   # Ce fichier
│
├── 📁 src/
│   ├── scraper.py                 # Script principal de scraping
│   └── google_sheets.py           # Module d'intégration Google Sheets
│
├── 📁 data/
│   ├── input/                     # Fichiers CSV d'entrée
│   │   └── grid.csv               # Exemple de fichier d'entrée
│   │
│   └── output/                    # Résultats de scraping
│       └── resultats_*.csv        # Fichiers de sortie horodatés
│
└── 📁 docs/
    ├── README_GENERAL.md          # Documentation détaillée
    ├── README_SCRAPER.md          # Documentation technique du scraper
    ├── ANTI_BLOCAGE.md            # Techniques anti-détection
    ├── OPTIMISATIONS.md           # Améliorations possibles
    ├── GS_INTEGRATION_PLAN.md     # Plan d'intégration Google Sheets
    └── GS_SETUP.md               # ⭐ Guide configuration Google Sheets
```

---

## 📊 Sites Scrapés

| Site | Statut | Couverture | Méthode de recherche |
|------|--------|------------|---------------------|
| **Medi-Market** | ✅ Actif | 91-92% | Par CNK (100% match si trouvé) |
| **Multipharma** | ✅ Actif | 98-100% | Par nom (double recherche: Grid + MediMarket) |
| **NewPharma** | ❌ Désactivé | 0% | Bloqué par anti-bot (403) |

---

## 📈 Format des Résultats

Les fichiers de sortie contiennent les colonnes suivantes:

| Colonne | Description |
|---------|-------------|
| `Nom_Produit` | Nom du produit (depuis le fichier d'entrée) |
| `CNK` | Code national du produit |
| `Prix_Base` | Prix de référence (depuis le fichier d'entrée) |
| `Prix_MediMarket` | Prix trouvé sur Medi-Market |
| `Prix_Multipharma` | Prix trouvé sur Multipharma |
| `Prix_NewPharma` | Prix NewPharma (désactivé) |
| `Match_MediMarket` | Score de correspondance (100% si trouvé) |
| `Match_Multipharma` | Score de correspondance du nom (0-100%) |
| `Match_Source_Multipharma` | Source du meilleur match ("Grid" ou "MediMarket") |
| `Match_NewPharma` | Score NewPharma (désactivé) |

### Indicateurs de Qualité

- ✅ **≥90%**: Haute confiance - Produit correctement identifié
- ⚠️ **70-89%**: Confiance moyenne - Vérification recommandée
- ❓ **<70%**: Faible confiance - Vérification manuelle nécessaire

---

## ⚙️ Configuration

### Prérequis

- **Python 3.11**
- **Environnement Conda**: `scraping`

### Installation

```bash
# Créer l'environnement
conda create -n scraping python=3.11

# Activer l'environnement
conda activate scraping

# Installer les dépendances
pip install requests beautifulsoup4 lxml rapidfuzz aiohttp
```

### Dépendances

- `requests`: Requêtes HTTP (Medi-Market)
- `beautifulsoup4`: Parsing HTML
- `lxml`: Parser HTML rapide
- `rapidfuzz`: Fuzzy matching pour les noms de produits
- `aiohttp`: Async HTTP client (Multipharma async)

---

## 📊 Performances

- **Temps d'exécution**: ~1 minute pour 101 produits (optimisé async)
- **Baseline (v1)**: ~5 minutes → **5× plus rapide !**
- **Taux de réussite global**: 95-98%
- **Score moyen de match**: 85.1%
- **Haute qualité (≥90%)**: 60% des résultats

### 🚀 Optimisations v6.0 (Async)

- ✅ Scraper Multipharma converti en async (aiohttp)
- ✅ Adaptive delays: réduits dynamiquement selon la charge
- ✅ Ramp-up progressif: démarrage à 10 workers → montée jusqu'à 30
- ✅ Connection pooling: 50 connexions max par host
- ✅ Batching par 10 produits pour contrôle graduel
- ✅ Scores en décimal (0,995 au lieu de 99,5%)

---

## 🛡️ Fonctionnalités Anti-Blocage

Le scraper intègre plusieurs techniques pour éviter d'être bloqué:

- ✅ Headers HTTP réalistes (User-Agent, Accept-Language, etc.)
- ✅ Délais adaptatifs entre requêtes (réduits dynamiquement)
- ✅ Pauses automatiques tous les 50 produits (1-3 secondes)
- ✅ Concurrence progressive (démarrage 10 workers → 30)
- ✅ Connection pooling pour réutilisation TCP
- ✅ Double recherche Multipharma pour meilleure précision

Pour plus de détails: `docs/ANTI_BLOCAGE.md`

---

## 📖 Documentation Complète

- **`docs/README_GENERAL.md`**: Documentation générale du projet
- **`docs/README_SCRAPER.md`**: Documentation technique du scraper
- **`docs/ANTI_BLOCAGE.md`**: Techniques anti-détection utilisées
- **`docs/OPTIMISATIONS.md`**: Pistes d'amélioration futures
- **`docs/GS_INTEGRATION_PLAN.md`**: Plan d'intégration Google Sheets
- **`docs/GS_SETUP.md`**: ⭐ **Guide de configuration Google Sheets**

---

## 💡 Exemples d'Utilisation

### Exemple 1: Scraping depuis fichier CSV

```bash
./run_scraper.sh data/input/produits_octobre.csv data/output/resultats_octobre.csv
```

### Exemple 2: Avec nom de fichier par défaut

```bash
# Renommez votre fichier en "grid.csv" dans data/input/
./run_scraper.sh
# Le résultat sera dans data/output/ avec horodatage automatique
```

### Exemple 3: Scraping depuis Google Sheets 🆕

```bash
conda activate scraping
python src/scraper.py --sheet test_pharma_scrap
```

Les résultats sont automatiquement écrits dans la Google Sheet !

### Exemple 4: Consulter les résultats CSV

```bash
# Voir les 10 premières lignes
head -10 data/output/resultats_20251012_160530.csv

# Compter le nombre de produits
wc -l data/output/resultats_20251012_160530.csv

# Rechercher un produit spécifique
grep "Caudalie" data/output/resultats_20251012_160530.csv
```

---

## ⚠️ Notes Importantes

1. **NewPharma désactivé**: Le site bloque les requêtes automatisées (erreur 403)
2. **Respect des serveurs**: Les délais anti-blocage respectent les sites scrapés
3. **Vérification des matchs**: Consultez toujours le score de match pour Multipharma
4. **Fichiers horodatés**: Les sorties incluent date et heure pour éviter les écrasements

---

## 🔧 Dépannage

### Le scraper ne démarre pas

```bash
# Vérifier que l'environnement conda est actif
conda activate scraping

# Vérifier les packages installés
pip list | grep -E "requests|beautifulsoup4|lxml|rapidfuzz"
```

### Erreurs de fichier d'entrée

```bash
# Vérifier que le fichier existe
ls -lh data/input/

# Vérifier le format du fichier (doit être séparé par des points-virgules)
head -5 data/input/votre_fichier.csv
```

### Résultats incomplets

- **Normal pour Medi-Market**: ~8-9% de produits non trouvés
- **Vérifier les scores de match**: Les scores <70% peuvent indiquer un mauvais produit
- **Consulter les logs**: Le scraper affiche les statistiques en temps réel

---

## 📞 Support

Pour toute question ou problème:
1. Consultez la documentation dans `docs/`
2. Vérifiez les scores de match dans les résultats
3. Examinez les logs d'exécution pour identifier les erreurs

---

## 📜 Historique

- **v1.0** (Oct 2025): Scrapers individuels par site
- **v2.0** (Oct 2025): Consolidation en master_scraper
- **v3.0** (Oct 2025): Ajout du matching avec scores
- **v4.0** (Oct 2025): Double recherche Multipharma
- **v5.0** (Oct 2025): Réorganisation professionnelle du projet
- **v6.0** (Oct 2025): Optimization async - 5× plus rapide ! 🚀

---

**Diego Claes** - LP_Pharma Project © 2025
