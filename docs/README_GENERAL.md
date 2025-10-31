# 🏥 LP_Pharma - Scraper de Prix Pharmaceutiques

Outil automatisé pour comparer les prix de produits pharmaceutiques sur plusieurs sites belges.

## 📋 Structure du Projet

```
LP_Pharma/
├── README.md                          # Ce fichier
├── run_master_scraper.sh             # Script de lancement rapide
├── grid-*.csv                        # Fichier d'entrée (produits à scraper)
├── resultats_final.csv               # Résultats consolidés
└── Scrap/
    ├── master_scraper.py             # ⭐ Script principal
    ├── README_MASTER_SCRAPER.md      # Documentation détaillée
    ├── ANTI_BLOCAGE.md               # Techniques anti-blocage
    └── OPTIMISATIONS.md              # Optimisations futures
```

## 🚀 Utilisation

### Lancement Rapide

```bash
./run_master_scraper.sh
```

### Lancement Manuel

```bash
python Scrap/master_scraper.py <fichier_grid.csv> <fichier_sortie.csv>
```

**Exemple:**
```bash
python Scrap/master_scraper.py grid-cc785a33-4e3f-45ba-9a33-948cba87b0fb.csv resultats_final.csv
```

## 📊 Format du Fichier d'Entrée (Grid)

Le fichier CSV d'entrée doit avoir le format suivant (séparateur: `;`):

```csv
name;CNK;prix
Caudalie Gel Douche;4487039;12
Caudalie Crème Mains;4886552;14,1
```

**Colonnes requises:**
- `name`: Nom du produit
- `CNK`: Code national du produit
- `prix`: Prix de base/référence

## 📈 Format de Sortie

Le fichier de résultats contient:

| Colonne | Description |
|---------|-------------|
| `Nom_Produit` | Nom du produit (depuis le grid) |
| `CNK` | Code national du produit |
| `Prix_Base` | Prix de référence du grid |
| `Prix_MediMarket` | Prix trouvé sur Medi-Market |
| `Prix_Multipharma` | Prix trouvé sur Multipharma |
| `Prix_NewPharma` | Prix NewPharma (désactivé - anti-bot) |
| `Match_MediMarket` | Score de correspondance (toujours 100% si trouvé) |
| `Match_Multipharma` | Score de correspondance du nom (0-100%) |
| `Match_Source_Multipharma` | Source du meilleur match ("Grid" ou "MediMarket") |
| `Match_NewPharma` | Score NewPharma (désactivé) |

## 🎯 Sites Scrapés

### ✅ Actifs
- **Medi-Market** (91-92% de couverture)
  - Recherche par CNK directement
  - Toujours 100% de match quand trouvé
  
- **Multipharma** (98-100% de couverture)
  - Recherche par nom de produit
  - Double recherche: nom du grid + nom trouvé sur Medi-Market
  - Garde le meilleur match
  - Score de fiabilité affiché

### ❌ Désactivés
- **NewPharma** (bloqué par protection anti-bot 403 Forbidden)

## 📊 Statistiques de Performance

- **Temps d'exécution**: ~12 minutes pour 101 produits
- **Couverture Medi-Market**: 91-92%
- **Couverture Multipharma**: 98-100%
- **Qualité des matchs Multipharma**:
  - Score moyen: 85.5%
  - Haute qualité (≥90%): 66%
  - Qualité moyenne (70-89%): 12%
  - Qualité faible (<70%): 21%
- **Sources des meilleurs matchs**:
  - Nom Grid: 81%
  - Nom MediMarket: 18%

## 🛡️ Fonctionnalités Anti-Blocage

- Headers réalistes (User-Agent, Accept-Language, etc.)
- Délais aléatoires entre requêtes (1-3s)
- Pauses automatiques tous les 20 produits (10-20s)
- Threading contrôlé (5 workers max)
- Pas de cache URL (évite la détection)

## 🔧 Configuration Requise

### Environnement Python

```bash
conda create -n scraping python=3.11
conda activate scraping
pip install requests beautifulsoup4 lxml rapidfuzz
```

### Packages Requis

- `requests`: Requêtes HTTP
- `beautifulsoup4`: Parsing HTML
- `lxml`: Parser HTML rapide
- `rapidfuzz`: Matching de noms (fuzzy matching)

## 📖 Documentation Détaillée

Pour plus d'informations, consultez:
- **`Scrap/README_MASTER_SCRAPER.md`**: Documentation complète du scraper
- **`Scrap/ANTI_BLOCAGE.md`**: Techniques anti-détection
- **`Scrap/OPTIMISATIONS.md`**: Améliorations futures possibles

## ⚠️ Notes Importantes

1. **NewPharma est désactivé**: Le site bloque toutes les requêtes automatisées avec une erreur 403
2. **Respect des sites**: Les délais anti-blocage respectent les serveurs des pharmacies
3. **Qualité des matchs**: Vérifiez le score de match pour Multipharma (colonne `Match_Multipharma`)
   - ✅ ≥90%: Haute confiance
   - ⚠️ 70-89%: Confiance moyenne
   - ❓ <70%: Vérification manuelle recommandée

## 🎯 Indicateurs Visuels Pendant l'Exécution

Le scraper affiche des indicateurs visuels pendant l'exécution:

- ✅ **Match ≥90%**: Haute qualité
- ⚠️ **Match 70-89%**: Qualité moyenne
- ❓ **Match <70%**: Qualité faible

## 📝 Exemple d'Utilisation Complète

```bash
# 1. Activer l'environnement
conda activate scraping

# 2. Lancer le scraper
python Scrap/master_scraper.py grid-cc785a33-4e3f-45ba-9a33-948cba87b0fb.csv resultats_final.csv

# 3. Consulter les résultats
head -20 resultats_final.csv
```

## 🔄 Historique du Projet

- **Initial**: Scrapers individuels pour chaque site
- **v1**: Consolidation dans master_scraper.py
- **v2**: Ajout du matching avec scores de fiabilité
- **v3**: Double recherche Multipharma (Grid + MediMarket)
- **v4**: Nettoyage et structure finale (octobre 2025)

## 👤 Auteur

Diego Claes - LP_Pharma Project
