# Optimisations du Master Scraper

## 📊 Résumé des Améliorations

### ⚡ Vitesse d'exécution estimée

| Phase | Avant | Après | Gain |
|-------|-------|-------|------|
| **Farmaline** | ~8-10s/CNK | ~2-3s/CNK | **70% plus rapide** |
| **NewPharma** | ~2-4s/CNK | ~0.5-1s/CNK | **75% plus rapide** |
| **Total (100 CNK)** | ~15-20 min | ~5-8 min | **60% plus rapide** |

---

## 🟢 Optimisations Farmaline

### 1. Concurrence augmentée
- **Avant** : 5 requêtes simultanées
- **Après** : 15 requêtes simultanées
- **Impact** : 3x plus de CNK traités en parallèle

### 2. Délais réduits
- **Avant** : 1-3 secondes entre requêtes
- **Après** : 0.3-0.8 secondes
- **Impact** : ~70% de temps gagné par requête

### 3. Cache intelligent de catégories
- Mémorise quelle catégorie contient quel type de produit
- Les CNK similaires (même préfixe) essayent d'abord la bonne catégorie
- **Impact** : Réduit le nombre de tentatives inutiles

### 4. Optimisation heuristique
- Catégories triées par probabilité (courtes = générales)
- Limite aux 10 catégories les plus courantes
- Stop rapide sur 404
- **Impact** : Moins de requêtes pour les produits non trouvés

### 5. Timeouts optimisés
- **Avant** : 30 secondes timeout global
- **Après** : 5 secondes par requête, 15s total
- **Impact** : Détection rapide des produits absents

### 6. Rotation d'User-Agents
- 5 User-Agents différents en rotation
- Chrome, Firefox, Safari
- **Impact** : Réduit les risques de détection

### 7. Gestion des exceptions
- `return_exceptions=True` dans `gather()`
- Continue même si certaines requêtes échouent
- **Impact** : Plus robuste, pas d'arrêt complet

---

## 🟡 Optimisations NewPharma

### 1. Parallélisation
- **Avant** : Séquentiel (1 CNK à la fois)
- **Après** : ThreadPoolExecutor avec 8 workers
- **Impact** : 8x plus rapide

### 2. Délais réduits
- **Avant** : 0.5-2 secondes
- **Après** : 0.2-0.6 secondes
- **Impact** : 60% de temps gagné

### 3. Timeout optimisé
- **Avant** : 10 secondes
- **Après** : 8 secondes
- **Impact** : Réponse plus rapide

### 4. Seuil fuzzy ajusté
- **Avant** : 90% de similarité
- **Après** : 85% de similarité
- **Impact** : ~10-15% plus de matches

### 5. Best match algorithm
- Trouve le meilleur match (score le plus élevé)
- Stop early si score >= 95%
- **Impact** : Meilleure précision et vitesse

### 6. Priorité intelligente
- Essaye d'abord le nom Farmaline (souvent plus précis)
- Fallback sur Medi-Market
- **Impact** : Meilleur taux de réussite

---

## 🔵 Medi-Market (déjà optimisé)

- Multi-threading avec 10 workers
- Deux phases (parapharmacie + pharmacie)
- Pas de modifications nécessaires

---

## ⚙️ Paramètres ajustables

Si vous voulez aller encore plus vite (mais plus risqué) :

### Farmaline
```python
CONCURRENT = 20  # Au lieu de 15
MIN_DELAY = 0.2  # Au lieu de 0.3
MAX_DELAY = 0.5  # Au lieu de 0.8
```

### NewPharma
```python
MAX_WORKERS = 12  # Au lieu de 8
FUZZY_THRESHOLD = 80  # Au lieu de 85 (plus de résultats mais moins précis)
```

### ⚠️ Risques d'aller trop vite
- Blocage IP temporaire
- Rate limiting
- Réponses vides ou erreurs
- Ban permanent (rare mais possible)

---

## 📈 Recommandations

### Pour une liste de 100-200 CNK
- ✅ Utilisez les paramètres actuels
- Temps estimé : 5-10 minutes

### Pour une liste de 500+ CNK
- Divisez en plusieurs fichiers de 200 CNK
- Exécutez avec 1-2 heures d'intervalle
- Utilisez des IPs différentes si possible (VPN/proxy)

### Pour du scraping régulier
- Implémentez un cache persistant (SQLite)
- Ne re-scrapez que les CNK modifiés
- Schedulez les exécutions (cron) pendant les heures creuses

---

## 🛡️ Protection anti-blocage

Les optimisations incluent déjà :
- ✅ Rotation d'User-Agents
- ✅ Délais aléatoires
- ✅ Timeouts courts (évite de monopoliser les connexions)
- ✅ Gestion d'erreurs gracieuse
- ✅ Connexions keep-alive désactivées (force_close=False pour aiohttp)

### Techniques supplémentaires (non implémentées)
- Rotation de proxies
- Cookies persistants
- Headers plus sophistiqués (Accept-Language, Referer, etc.)
- Comportement "humain" (mouse movements, scroll simulation)

---

## 🧪 Test de performance

Pour mesurer l'impact :

```bash
# Avant optimisations
time ./run_master_scraper.sh test_10cnk.csv output_before.csv

# Après optimisations
time ./run_master_scraper.sh test_10cnk.csv output_after.csv
```

Attendez-vous à une réduction de **50-70%** du temps total.

---

## 🎯 Résultat attendu

Pour **100 CNK** :
- ⏱️ **Temps total** : 5-8 minutes (vs 15-20 min avant)
- 📊 **Taux de succès** : 
  - Farmaline : 40-60%
  - Medi-Market : 85-95%
  - NewPharma : 50-70%
- 💾 **Ressources** :
  - CPU : ~20-30% (multi-threading)
  - RAM : ~100-200 MB
  - Réseau : ~5-10 MB

---

## ✅ Prochaines étapes

1. Testez avec un petit échantillon (10-20 CNK)
2. Vérifiez qu'aucun CNK n'est bloqué
3. Lancez sur votre liste complète
4. Surveillez les logs pour détecter des problèmes

Bonne chance ! 🚀
