# 🚨 Rapport de Test Anti-Détection - 18 Oct 2025

## Résumé Exécutif

**Status**: ❌ Les deux sites bloquent le scraping

| Site | Status | Problème | Solution Recommandée |
|------|--------|----------|---------------------|
| **Farmaline** | ❌ 404 | CNK non trouvé ou structure URL incorrecte | Vérifier structure URL + tester avec CNK valide |
| **NewPharma** | ❌ 403 | **Cloudflare actif** | VPS Belgique ou Playwright + cloudscraper |

---

## Détails des Tests

### Test Configuration
- **CNK testé**: `0168536` (Dafalgan 500mg)
- **Anti-détection activé**:
  - ✅ 13 User-Agents différents en rotation
  - ✅ Délais humains (0.5-30s avec pauses aléatoires)
  - ✅ Accept-Language rotation (fr-FR, fr-BE, nl-BE)
  - ✅ Headers complets (Sec-Fetch-*, DNT, Cache-Control)
  - ✅ Error tracking (403/429)

### Farmaline - Analyse

**URLs testées**:
```
https://www.farmaline.be/fr/medicaments/BE00168536/ → 404
https://www.farmaline.be/fr/douleur-fievre-grippe/BE00168536/ → 404
https://www.farmaline.be/fr/bien-etre/BE00168536/ → 404
https://www.farmaline.be/fr/sante/BE00168536/ → 404
```

**Problème identifié**: 
- Pas de blocage anti-bot détecté (aucun 403/429)
- Produit non trouvé (404) → Soit le CNK n'existe pas, soit la structure d'URL est différente

**Actions à faire**:
1. Vérifier manuellement sur https://www.farmaline.be/ si ce CNK existe
2. Chercher la vraie structure d'URL (peut-être différente de `/fr/{cat}/BE0{cnk}/`)
3. Tester avec un CNK qu'on sait qui existe sur Farmaline

### NewPharma - Analyse

**URL testée**:
```
https://www.newpharma.be/fr/search-results/search.html?q=Dafalgan+500mg → 403 Forbidden
```

**Problème identifié**: **Cloudflare Challenge**
- Erreur 403 immédiate → Protection anti-bot active (Cloudflare)
- L'anti-détection basique (User-Agent rotation) ne suffit pas
- Cloudflare détecte probablement :
  - Absence de JavaScript
  - Pas de cookies Cloudflare
  - Pattern de requêtes suspects

**Preuve**: NewPharma utilise Cloudflare (visible dans les headers et la page d'accueil)

---

## 🎯 Solutions Recommandées

### Option 1: VPS en Belgique ⭐ **RECOMMANDÉ**
**Pourquoi**: IP résidentielle belge = pas suspect
**Coût**: 5€/mois
**Fournisseurs**:
- OVH Belgique
- DigitalOcean Bruxelles
- Hetzner

**Avantages**:
- ✅ IP locale (moins de blocages)
- ✅ Pas de limite de volume
- ✅ Fonctionne pour tous les sites
- ✅ Rapide (pas de proxy externe)

**Mise en place**:
```bash
# 1. Louer VPS avec IP belge
# 2. Installer Python et dépendances
# 3. Lancer le scraper depuis le VPS
ssh user@vps-belgique
cd LP_Pharma
./run_scraper.sh
```

---

### Option 2: Playwright + Cloudflare Bypass
**Pourquoi**: Navigateur réel qui exécute JavaScript
**Coût**: 0€ (mais plus lent)

**Installation**:
```bash
conda activate scraping
pip install playwright cloudscraper
playwright install chromium
```

**Modification du scraper**:
```python
from playwright.async_api import async_playwright

async def scrape_newpharma_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 ...",
            locale="fr-BE",
            timezone_id="Europe/Brussels",
        )
        
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")
        
        # Cloudflare challenge résolu automatiquement
        content = await page.content()
        await browser.close()
        
        return content
```

**Avantages**:
- ✅ Bypass Cloudflare automatiquement
- ✅ Exécute JavaScript (comme un vrai navigateur)
- ✅ Gratuit

**Désavantages**:
- ❌ 10-20x plus lent
- ❌ Consomme beaucoup de RAM
- ❌ Plus complexe à debugger

---

### Option 3: ScraperAPI (Proxies Résidentiels)
**Pourquoi**: Service clé-en-main avec rotation IP automatique
**Coût**: ~2€/mois (1000 requêtes ≈ 200 CNKs × 2 sites)

**Code**:
```python
import requests

SCRAPER_API_KEY = "votre_clé"

def scrape_with_proxy(url):
    payload = {
        'api_key': SCRAPER_API_KEY,
        'url': url,
        'country_code': 'be',  # Proxy Belgique
        'render': 'false',     # Pas de JS (plus rapide)
    }
    return requests.get('http://api.scraperapi.com', params=payload)

# Utilisation
response = scrape_with_proxy('https://www.newpharma.be/...')
```

**Avantages**:
- ✅ Simple (2 lignes de code)
- ✅ IP résidentielle différente à chaque requête
- ✅ Gère Cloudflare automatiquement

**Désavantages**:
- ❌ Payant (mais très abordable)
- ❌ Limite de volume mensuel
- ❌ Plus lent (requête via proxy externe)

---

### Option 4: cloudscraper (Module Python)
**Pourquoi**: Contourne Cloudflare sans navigateur
**Coût**: 0€

**Installation**:
```bash
pip install cloudscraper
```

**Code**:
```python
import cloudscraper

scraper = cloudscraper.create_scraper()
response = scraper.get('https://www.newpharma.be/...')
# Cloudflare challenge résolu automatiquement
```

**Avantages**:
- ✅ Gratuit
- ✅ Plus rapide que Playwright
- ✅ Simple à implémenter

**Désavantages**:
- ❌ Peut ne pas fonctionner si Cloudflare évolue
- ❌ Moins fiable que Playwright

---

## 📝 Plan d'Action Recommandé

### Phase 1: Test avec cloudscraper (30 min)
```bash
# 1. Installer cloudscraper
pip install cloudscraper

# 2. Modifier scraper.py pour utiliser cloudscraper
# 3. Tester avec --limit 5
python src/scraper.py --sheet test_pharma_scrap --limit 5
```

**Si ça marche**: ✅ Problème résolu gratuitement
**Si ça ne marche pas**: Passer à Phase 2

---

### Phase 2: VPS Belgique (1h setup)
```bash
# 1. Louer VPS chez OVH (~5€/mois)
# 2. Installer environnement Python
# 3. Copier le projet sur le VPS
# 4. Lancer depuis le VPS

# SSH vers VPS
ssh user@vps-belgique.ovh.net
git clone <votre-repo>
cd LP_Pharma
./install.sh
./run_scraper.sh
```

**Résultat attendu**: ✅ 95%+ de succès sur Farmaline et NewPharma

---

## 🔍 Vérifications Immédiates

### 1. Vérifier CNK sur Farmaline manuellement
1. Aller sur https://www.farmaline.be/fr/
2. Chercher "Dafalgan 500mg" dans la barre de recherche
3. Noter la vraie URL du produit
4. Adapter le scraper en conséquence

### 2. Tester cloudscraper immédiatement
```python
# test_cloudscraper.py
import cloudscraper

scraper = cloudscraper.create_scraper()
response = scraper.get('https://www.newpharma.be/fr/search-results/search.html?q=dafalgan')

print(f"Status: {response.status_code}")
print(f"Bloqué par Cloudflare: {'Access denied' in response.text or 'Attention Required' in response.text}")
```

---

## 💡 Recommandation Finale

**Pour vous** (besoin de scraper Farmaline + NewPharma sans se faire détecter):

1. **Court terme** (aujourd'hui) : Tester cloudscraper (gratuit, 30 min)
2. **Moyen terme** (cette semaine) : Louer VPS en Belgique si cloudscraper ne marche pas (5€/mois)
3. **Long terme** : Garder l'anti-détection actuelle pour Medi-Market + Multipharma (ils fonctionnent bien)

**Budget total**: 0€ à 5€/mois maximum

---

**Généré le**: 18 Oct 2025  
**Auteur**: Diego Claes - LP_Pharma Project
