# 🛡️ Guide Complet Anti-Détection et Evasion de Blocage

## Table des matières
1. [Diagnostique des blocages](#diagnostique)
2. [Solutions par niveau de risque](#solutions)
3. [Stratégies complètes](#strategies)
4. [Implémentation recommandée](#implementation)
5. [Monitoring et alertes](#monitoring)

---

## 🔍 Diagnostique des Blocages {#diagnostique}

### Pourquoi Farmaline et NewPharma bloquent ?

| Site | Type de blocage | Détection | Difficulté |
|------|-----------------|-----------|-----------|
| **NewPharma** | 403 Forbidden | IP + Pattern | Très élevée |
| **Farmaline** | 403 Forbidden | User-Agent + Pattern | Élevée |
| **Medi-Market** | ✅ Permissif | Minimal (délais respectés) | Faible |
| **Multipharma** | ✅ Permissif | Minimal (async ok) | Faible |

### Signaux de détection

```
❌ DÉTECTÉ = Erreur 403/429 régulièrement
- Trop de requêtes par seconde
- User-Agent anormal
- Pattern de requêtes trop régulier
- Pas de pauses entre sessions
- IP uniquement (datacenter)
- Headers vides/incomplets
```

---

## 🎯 Solutions par Niveau de Risque {#solutions}

### Niveau 1: Sans Risque (Déjà implémenté ✅)
**Coût**: Gratuit | **Effort**: Faible | **Efficacité**: 80%

```
✅ Connection pooling (HTTPAdapter)
✅ Headers réalistes (User-Agent, Accept-Language)
✅ Délais aléatoires (0.1-0.8s)
✅ Pauses périodiques (tous les 50 produits)
✅ Timeout court (fail-fast)
✅ Async pour concurrence efficace
```

**Quand l'utiliser**: ✅ Medi-Market, Multipharma
**Limitations**: ❌ Inefficace sur Farmaline/NewPharma

---

### Niveau 2: Modéré (Juste au-dessus du safe)
**Coût**: Gratuit | **Effort**: Moyen | **Efficacité**: 85%

#### 2.1 Rotation de User-Agents avancée
```python
# Au lieu d'un seul User-Agent fixe
USER_AGENTS = [
    # Chrome versions récentes
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # Firefox versions récentes
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:121.0) Gecko/20100101 Firefox/121.0",
    
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    
    # Mobile (parfois moins bloqué)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

# Inclure aussi les Accept-Language variés
ACCEPT_LANGUAGES = [
    "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,fr;q=0.8",
    "nl-BE,nl;q=0.9,fr;q=0.8",  # Néerlandais (Belgique)
]
```

#### 2.2 Délais intelligents
```python
# Au lieu de délais fixes
import time
import random

# Délais variables selon contexte
DELAY_SHORT = random.uniform(0.1, 0.3)   # Entre deux recherches simples
DELAY_MEDIUM = random.uniform(0.5, 1.2)  # Entre deux produits
DELAY_LONG = random.uniform(2, 5)        # Pause de sécurité

# Ajouter de l'aléa réaliste (comportement humain)
def human_like_delay():
    """Simule un comportement humain avec pauses irrégulières"""
    choice = random.random()
    if choice < 0.1:  # 10% de chance: pause longue (distraction)
        return random.uniform(5, 15)
    elif choice < 0.3:  # 20% de chance: pause moyenne
        return random.uniform(2, 5)
    else:  # 70% de chance: pause courte
        return random.uniform(0.5, 2)

time.sleep(human_like_delay())
```

#### 2.3 Rotation d'adresses IP locales
```python
# Si vous avez plusieurs connexions locales (VPN, proxy local)
PROXIES = [
    None,  # Pas de proxy (votre IP)
    "socks5://127.0.0.1:9050",  # Tor local (lent mais très anonyme)
    "http://proxy1.local:8080",
    "http://proxy2.local:8080",
]

# Rotation aléatoire
import random
proxy = random.choice(PROXIES)
response = session.get(url, proxies={"https": proxy} if proxy else {})
```

**Quand l'utiliser**: Pour tenter Farmaline une 2e fois
**Limitations**: Besoin de VPN/proxy local, plus lent

---

### Niveau 3: Élevé (Solutions sophistiquées)
**Coût**: 10-100€/mois | **Effort**: Élevé | **Efficacité**: 90-95%

#### 3.1 Service de Proxy Résidentiels
```python
# Utiliser un service comme Bright Data, ScraperAPI, Oxylabs
# Chaque requête sort d'une IP différente (résidentielle = réelle personne)

import requests

# Option A: ScraperAPI (simple)
SCRAPER_API_KEY = "votre_clé"

def scrape_with_scraper_api(url):
    payload = {
        'api_key': SCRAPER_API_KEY,
        'url': url,
        'render': 'false',
        'country_code': 'be',  # Proxy Belgique
    }
    return requests.get('http://api.scraperapi.com', params=payload)

# Option B: Bright Data (contrôle fin)
proxy_url = "http://user:password@proxy.provider:port"
response = session.get(url, proxies={"https": proxy_url})

# Prix ScraperAPI: ~0.5-1€ par 1000 requêtes
# Prix Bright Data: ~10-50€/mois selon volume
```

**Avantages**:
- ✅ Une IP différente à chaque requête
- ✅ IPs résidentielles (moins suspectes)
- ✅ Géolocalisation (peut choisir pays)
- ✅ Gestion automatique des rotations

**Désavantages**:
- ❌ Coûteux
- ❌ Plus lent (requête passe par proxy)
- ❌ Limite de volume par mois

**Fournisseurs recommandés**:
1. **ScraperAPI** - Simple, pas de config proxy
2. **Bright Data** - Plus de contrôle, meilleur support
3. **Oxylabs** - Très fiable pour sites complexes
4. **Luminati** - De Bright Data, même tech

---

#### 3.2 Browser Automation avec Playwright
```python
# Les sites détectent les bots en testant JavaScript
# Solution: utiliser un navigateur réel

from playwright.async_api import async_playwright
import asyncio

async def scrape_with_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            # Désactiver détection headless
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Context avec options réalistes
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="fr-BE",
            timezone_id="Europe/Brussels",
            # Simuler géolocalisation
            geolocation={"latitude": 50.8503, "longitude": 4.3517},
            permissions=["geolocation"],
        )
        
        page = await context.new_page()
        
        # Attendre que la page se charge complètement
        await page.goto(url, wait_until="networkidle")
        
        # Récupérer le HTML rendu (après JavaScript)
        content = await page.content()
        
        await browser.close()
        return content

# Utiliser dans le scraper
# html = await scrape_with_playwright(url)
```

**Avantages**:
- ✅ Exécute JavaScript
- ✅ Bloque les détecteurs de bots
- ✅ Contrôle fin du comportement
- ✅ Peut cliquer, remplir formulaires

**Désavantages**:
- ❌ Très lent (5-10x plus)
- ❌ Consomme beaucoup RAM
- ❌ Complexe à debugger

**Quand l'utiliser**: Seulement si Farmaline/NewPharma exigent JavaScript

---

#### 3.3 Cloudflare Bypass
Farmaline/NewPharma utilisent probablement Cloudflare pour WAF.

```python
# Option 1: cloudflare-scrape (mais obsolète)
# Option 2: cloudscraper
import cloudscraper

scraper = cloudscraper.create_scraper()
response = scraper.get(url)  # Contourne automatiquement Cloudflare

# Option 3: Playwright + Cloudflare bypass
# (Playwright passe souvent naturellement)
```

**Installation**:
```bash
pip install cloudscraper
# ou
pip install cf-clearance
```

---

### Niveau 4: Extrême (Solutions légales mais sophistiquées)
**Coût**: 100€+ | **Effort**: Très élevé | **Efficacité**: 98%+

#### 4.1 API officielle
```python
# Contacter le site pour une API officielle
# Farmaline/NewPharma pourraient avoir une API B2B

# Avantages:
# ✅ Légal et garanti
# ✅ Plus rapide et fiable
# ✅ Support officiel
# ❌ Accès limité ou payant
```

#### 4.2 Hébergement en datacenter belgique
```python
# Louer un VPS en Belgique
# Les sites bloquent souvent les datacenters non-belgiques
# VPS à partir de 5-10€/mois chez Linode, DigitalOcean, OVH
```

#### 4.3 Selenium + UndetectedChromeDriver
```python
from undetected_chromedriver import Chrome
import time

driver = Chrome()
driver.get(url)
time.sleep(2)  # Laisser charger

# C'est un navigateur normal, très difficile à détecter
html = driver.page_source
driver.quit()
```

---

## 📋 Stratégies Complètes {#strategies}

### Stratégie A: "Safe & Slow" (Recommandé initialement)
**Cible**: Medi-Market ✅ + Multipharma ✅
**Temps**: 1 min | **Coût**: 0€ | **Risque**: 0%

```
1. Garder la config actuelle (async + adaptive delays)
2. Augmenter délais de sécurité (2s entre produits)
3. Ajouter variation User-Agents
4. Arrêter si erreur 429 après 2 tentatives
```

---

### Stratégie B: "Fast & Agile" (Revenir aux 2 sites)
**Cible**: Farmaline ⚠️ + NewPharma ⚠️
**Temps**: 2 min | **Coût**: 5-10€ | **Risque**: Moyen

```
Niveau 2 + Niveau 3.1:
1. Rotation User-Agents complète (8 agents)
2. Human-like delays avec pauses irrégulières
3. Ajouter Accept-Language variables
4. ScraperAPI pour 20% des requêtes Farmaline
5. Monitoring des erreurs 403
6. Backoff exponentiel: 1s → 5s → 30s
```

**Implémentation**:
```python
# Pseudocode
def scrape_farmaline_safe(cnk_list):
    attempt = 0
    max_attempts = 3
    
    while attempt < max_attempts:
        try:
            # 80% requêtes directes, 20% via ScraperAPI
            if random.random() < 0.8:
                response = session.get(url, headers=rotate_headers())
            else:
                response = scrape_with_scraper_api(url)
            
            if response.status_code == 200:
                return parse(response)
            elif response.status_code == 403:
                raise BlockedException()
                
        except BlockedException:
            attempt += 1
            wait = 2 ** attempt  # 2s, 4s, 8s...
            print(f"⏳ Blocked, wait {wait}s")
            time.sleep(wait)
    
    return None
```

---

### Stratégie C: "Maximum Coverage" (Tous les sites)
**Cible**: Medi-Market ✅ + Multipharma ✅ + Farmaline ✅ + NewPharma ✅
**Temps**: 3-5 min | **Coût**: 20-50€/mois | **Risque**: Faible si bien configuré

```
Niveau 3 complet:
1. ScraperAPI pour Farmaline/NewPharma
2. Playwright fallback pour pages complexes
3. Cloudscraper pour Cloudflare
4. Géolocalisation Belgique
5. Délais adaptatifs
6. Monitoring complet
```

**Coûts mensuels**:
- ScraperAPI: 0.5€ par 1000 req = ~2€/mois (200 req = 101 CNKs × 2 sites)
- Playwright: Gratuit (RAM)
- Total: ~2€/mois

---

### Stratégie D: "Datacenter Belgique" (Optimal)
**Cible**: Tous les sites
**Temps**: 1-2 min | **Coût**: 5€/mois | **Risque**: Très faible

```
Au lieu de proxies externes:
1. Louer VPS OVH/DigitalOcean en Belgique (~5€/mois)
2. Lancer scraper depuis la VM
3. Tous les sites voient une IP résidentielle belgique
4. Pas besoin de proxies payants
5. Plus rapide que ScraperAPI
```

**Exemple OVH**:
- VPS 1GB RAM: 5€/mois
- Localisation: Belgique/Pays-Bas
- Accès SSH: Oui

---

## 🛠️ Implémentation Recommandée {#implementation}

### Phase 1: Aujourd'hui (Gratuit)
```python
# Ajouter au scraper.py

import random
from collections import deque

# Rotation d'User-Agents complète
USER_AGENTS_EXTENDED = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

ACCEPT_LANGUAGES = [
    "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,fr;q=0.8",
]

def rotate_headers():
    """Génère des headers réalistes et variables"""
    return {
        "User-Agent": random.choice(USER_AGENTS_EXTENDED),
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }

def human_like_delay():
    """Délais réalistes avec comportement humain"""
    choice = random.random()
    if choice < 0.05:  # 5%: pause distraction
        return random.uniform(10, 30)
    elif choice < 0.15:  # 10%: pause moyenne
        return random.uniform(3, 8)
    else:  # 85%: délai normal
        return random.uniform(0.5, 2)
```

**Coût**: 0€ | **Gain attendu**: +5% de pas de blocages

---

### Phase 2: Si toujours bloqué (5€ + temps)
```bash
# Option A: Louer VPS Belgique (recommandé)
# Chez OVH: VPS 1GB à 5€/mois
# SSH dessus et relancer le scraper

# Option B: Ajouter ScraperAPI (code minimal)
pip install requests

# Dans le scraper:
def scrape_farmaline_with_proxy(url):
    payload = {
        'api_key': 'votre_clé_scraper_api',
        'url': url,
    }
    return requests.get('http://api.scraperapi.com', params=payload)
```

**Coût**: 5€/mois (VPS) ou ~2€/mois (ScraperAPI)
**Gain attendu**: 95%+ de succès

---

### Phase 3: Si vraiment nécessaire (Playwright)
```bash
pip install playwright
playwright install chromium
```

**Coût**: 0€ | **Perf**: -80% (très lent)

---

## 📊 Monitoring et Alertes {#monitoring}

### Tracker les erreurs
```python
error_tracker = {
    'farmaline_403': 0,
    'newpharma_403': 0,
    'medi_market_429': 0,
    'multipharma_429': 0,
}

def log_error(site, error_code):
    error_tracker[f'{site}_{error_code}'] += 1
    
    if error_tracker[f'{site}_{error_code}'] > 3:
        print(f"⚠️ ALERTE: {site} bloque ({error_code})")
        # Envoyer email, Slack, etc.

# À la fin du scraping
print("\n📊 Résumé des erreurs:")
for error_type, count in error_tracker.items():
    if count > 0:
        print(f"  {error_type}: {count}")
```

### Dashboard simple
```python
# Ajouter au README output
def print_health_report():
    print("""
    🏥 SCRAPER HEALTH REPORT
    ========================
    Medi-Market:  ✅ 91/101 (OK)
    Multipharma:  ✅ 99/101 (OK)
    Farmaline:    ⚠️  0/101 (BLOCKED - 403)
    NewPharma:    ⚠️  0/101 (BLOCKED - 403)
    
    ACTIONS RECOMMANDÉES:
    1. Ajouter User-Agent rotation (gratuit)
    2. Implémenter délais humains (gratuit)
    3. VPS Belgique ou ScraperAPI (5-10€/mois)
    """)
```

---

## 🎯 Tableau Décisionnel

| Situation | Action | Coût | Temps |
|-----------|--------|------|-------|
| Medi-Market OK | Garder config actuelle | 0€ | 1 min |
| Multipharma OK | Garder config actuelle | 0€ | 1 min |
| Farmaline bloque | Phase 1 (User-Agents) | 0€ | 30 min |
| NewPharma bloque | Phase 1 (User-Agents) | 0€ | 30 min |
| Toujours bloqué | Phase 2 (VPS/ScraperAPI) | 5€ | 1h |
| Pages complexes | Phase 3 (Playwright) | 0€ | 2h |
| Maximum fiabilité | Phase 2 + Dashboard | 5€ | 1h |

---

## ⚖️ Considérations Légales

- **Robots.txt**: Vérifier que les sites n'interdisent pas le scraping
- **Terms of Service**: Lire les conditions (possibilité de mentions)
- **Respect**: Délais suffisants pour ne pas surcharger les serveurs
- **API officielle**: Contacter d'abord pour une intégration légale

**Statut légal du scraping en Belgique**:
- ✅ Légal si respecte les serveurs et pas violation TOS
- ❌ Illégal si bypasse authentification ou viole TOS explicitement
- ⚠️ Gris si les données sont publiques mais site refuse

---

## 📚 Ressources

### Documentation
- Playwright: https://playwright.dev/
- ScraperAPI: https://www.scraperapi.com/
- Bright Data: https://brightdata.com/
- Cloudscraper: https://github.com/VenoM1337/cloudscraper

### Outils
- cURL headers tester: https://curl.se/
- User-Agent checker: https://www.whoishostingthis.com/tools/user-agent/
- IP check: https://www.whatismyipaddress.com/

### Communauté
- Stack Overflow: tag `web-scraping`
- Reddit: r/webscraping
- GitHub: awesome-web-scraping

---

## 🚀 Prochaines Étapes

1. **Aujourd'hui**: Implémenter Phase 1 (User-Agents, délais humains)
2. **Semaine prochaine**: Tester avec Phase 1, mesurer résultats
3. **Si encore bloqué**: Évaluer Phase 2 (VPS ou ScraperAPI)
4. **Monitoring**: Ajouter dashboard pour tracker la fiabilité

---

**Dernière mise à jour**: 18 Oct 2025
**Auteur**: Diego Claes - LP_Pharma Project
