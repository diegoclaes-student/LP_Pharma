# Master Scraper - Guide d'utilisation

## Description

Le script `master_scraper.py` orchestre le scraping de 3 sites de pharmacies en ligne :
- 🟢 **Farmaline** (www.farmaline.be)
- 🔵 **Medi-Market** (medi-market.be + pharmacy-medi-market.be)
- 🟡 **NewPharma** (www.newpharma.be)

Il produit un fichier CSV consolidé avec les prix des 3 sites pour chaque CNK.

## Prérequis

### Dépendances Python
```bash
pip install requests beautifulsoup4 lxml aiohttp aiohttp-retry rapidfuzz fake-useragent
```

Ou si vous avez un environnement conda :
```bash
conda activate scraping
```

## Utilisation

### Syntaxe de base
```bash
python Scrap/master_scraper.py <fichier_input_cnk> <fichier_output_consolide>
```

### Exemple
```bash
python Scrap/master_scraper.py CNK_111025.csv resultats_consolides_111025.csv
```

### Format du fichier d'entrée
Le fichier d'entrée doit être un CSV avec les CNK (une par ligne) :
```csv
CNK
1234567
2345678
3456789
```

ou simplement :
```
1234567
2345678
3456789
```

### Format du fichier de sortie
Le script génère un CSV avec 4 colonnes (séparateur `;`) :
```csv
CNK;Prix_Farmaline;Prix_MediMarket;Prix_NewPharma
1234567;12.50;11.90;13.20
2345678;NA;8.75;9.00
3456789;15.30;NA;14.99
```

- `NA` indique qu'un produit n'a pas été trouvé sur ce site.

## Fonctionnement

Le script exécute 3 phases séquentielles :

### Phase 1 : Medi-Market (multi-thread)
- Scrape le site parapharmacie Medi-Market
- Si non trouvé, scrape le site pharmacie Medi-Market
- Utilise 10 threads en parallèle

### Phase 2 : Farmaline (asynchrone)
- Scrape Farmaline de manière asynchrone
- Utilise 5 requêtes concurrentes
- Gestion automatique des catégories

### Phase 3 : NewPharma (recherche fuzzy)
- Utilise les noms de produits trouvés par Farmaline et Medi-Market
- Effectue une recherche fuzzy (similarité > 90%)
- Parse les données JSON de la page

### Phase 4 : Consolidation
- Fusionne les résultats des 3 sites
- Génère le fichier CSV final
- Affiche les statistiques de couverture

## Statistiques affichées

À la fin de l'exécution, vous verrez :
```
📈 Statistiques de couverture:
  • Total CNK: 150
  • Farmaline: 120 (80.0%)
  • Medi-Market: 135 (90.0%)
  • NewPharma: 110 (73.3%)
```

## Performances

- **Vitesse** : Environ 2-5 secondes par CNK (dépend de la disponibilité et des délais anti-détection)
- **Parallélisation** : Medi-Market et Farmaline sont optimisés avec multi-threading/async
- **Respectueux** : Délais aléatoires entre requêtes pour éviter de surcharger les sites

## Fichiers temporaires

Le script crée un dossier `Scrap/temp_master/` pour stocker les résultats intermédiaires.
Ce dossier peut être supprimé après l'exécution.

## Erreurs courantes

### "Module not found: aiohttp"
```bash
pip install aiohttp aiohttp-retry
```

### "Module not found: rapidfuzz"
```bash
pip install rapidfuzz
```

### "fichier d'entrée introuvable"
Vérifiez que le chemin vers votre fichier CNK est correct.

## Conseils

1. **Test avec un petit fichier** : Commencez avec 5-10 CNK pour valider
2. **Vérifiez votre connexion** : Le script nécessite une connexion internet stable
3. **Exécution en arrière-plan** : Pour de grandes listes, utilisez `nohup` ou `screen`

```bash
nohup python Scrap/master_scraper.py input.csv output.csv > scraping.log 2>&1 &
```

## Support

En cas de problème, vérifiez :
1. Les logs affichés dans le terminal
2. Votre connexion internet
3. Que les sites ne bloquent pas temporairement votre IP

## Améliorations futures

- [ ] Support pour d'autres sites de pharmacies
- [ ] Export en format Excel
- [ ] Interface graphique
- [ ] Système de reprise en cas d'interruption
- [ ] Cache intelligent pour éviter de re-scraper les mêmes CNK
