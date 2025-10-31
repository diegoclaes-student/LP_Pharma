#!/usr/bin/env python3 -u
"""
Script master pour scraper Farmaline, Medi-Market, NewPharma et Multipharma en une seule exécution.
Produit un CSV consolidé avec les prix des 4 sites.

Usage:
    python master_scraper.py <input_cnk_file> <output_file>

Exemple:
    python master_scraper.py CNK_111025.csv resultats_consolides.csv
"""

import sys
import os

# Force unbuffered output pour voir l'avancement en temps réel
if not sys.flags.optimize:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

import csv
import time
import subprocess
import asyncio
import json
import random
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# Configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
TEMP_DIR = SCRIPT_DIR / "temp_master"
TEMP_DIR.mkdir(exist_ok=True)

# ============================================================================
# 🛡️ FONCTION HELPER: Print avec flush automatique (affichage en temps réel)
# ============================================================================
def print_live(message="", end="\n"):
    """Affiche un message et force l'affichage immédiat (pas de buffer)."""
    print(message, end=end, flush=True)

# ============================================================================
# 🛡️ ANTI-DÉTECTION: User-Agents, Headers, Délais
# ============================================================================

# Liste étendue de User-Agents réalistes (Chrome, Firefox, Safari, Edge, Mobile)
USER_AGENTS_EXTENDED = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Mobile Chrome Android
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    # Mobile Safari iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

# Accept-Language variés (français, néerlandais belgique)
ACCEPT_LANGUAGES = [
    "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "fr-BE,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "nl-BE,nl;q=0.9,fr;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,fr;q=0.8",
]

# Tracker global des erreurs de blocage (403, 429)
ERROR_TRACKER = {
    'farmaline_403': 0,
    'farmaline_429': 0,
    'newpharma_403': 0,
    'newpharma_429': 0,
    'medi_market_403': 0,
    'medi_market_429': 0,
    'multipharma_403': 0,
    'multipharma_429': 0,
}

def rotate_headers():
    """
    Génère des headers HTTP réalistes et variables pour éviter la détection.
    Rotation User-Agent + Accept-Language + tous les headers modernes.
    """
    return {
        "User-Agent": random.choice(USER_AGENTS_EXTENDED),
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

def human_like_delay():
    """
    Simule un comportement humain avec délais aléatoires et pauses irrégulières.
    
    - 5% de chance: pause longue (10-30s) = distraction, pause café
    - 10% de chance: pause moyenne (3-8s) = réflexion
    - 85% de chance: délai normal (0.5-2s) = navigation normale
    
    Returns:
        float: Nombre de secondes à attendre
    """
    choice = random.random()
    if choice < 0.05:  # 5%: pause longue
        return random.uniform(10, 30)
    elif choice < 0.15:  # 10%: pause moyenne
        return random.uniform(3, 8)
    else:  # 85%: délai normal
        return random.uniform(0.5, 2)

def log_blocking_error(site, error_code):
    """
    Enregistre une erreur de blocage (403, 429) pour monitoring.
    
    Args:
        site: Nom du site ('farmaline', 'newpharma', 'medi_market', 'multipharma')
        error_code: Code HTTP (403, 429)
    """
    key = f'{site}_{error_code}'
    if key in ERROR_TRACKER:
        ERROR_TRACKER[key] += 1
        
        # Alerte si trop d'erreurs
        if ERROR_TRACKER[key] >= 5:
            print(f"\n⚠️ ALERTE: {site.upper()} bloque fréquemment (code {error_code}, {ERROR_TRACKER[key]} occurrences)")
            print(f"   → Considérez augmenter les délais ou utiliser un VPS/proxy")

def print_blocking_report():
    """Affiche un rapport des erreurs de blocage détectées pendant le scraping."""
    total_errors = sum(ERROR_TRACKER.values())
    if total_errors == 0:
        print("\n✅ Aucune erreur de blocage détectée (403/429)")
        return
    
    print("\n" + "="*60)
    print("⚠️  RAPPORT DES ERREURS DE BLOCAGE")
    print("="*60)
    
    for site in ['farmaline', 'newpharma', 'medi_market', 'multipharma']:
        errors_403 = ERROR_TRACKER.get(f'{site}_403', 0)
        errors_429 = ERROR_TRACKER.get(f'{site}_429', 0)
        total_site = errors_403 + errors_429
        
        if total_site > 0:
            print(f"\n🔴 {site.upper()}:")
            if errors_403 > 0:
                print(f"   • 403 Forbidden: {errors_403} fois")
            if errors_429 > 0:
                print(f"   • 429 Too Many Requests: {errors_429} fois")
    
    print("\n💡 Actions recommandées:")
    print("   1. Augmenter les délais (human_like_delay déjà activé)")
    print("   2. Louer un VPS en Belgique (~5€/mois)")
    print("   3. Utiliser ScraperAPI pour proxies résidentiels (~2€/mois)")
    print("   4. Consulter docs/ANTI_DETECTION_AVANCEE.md pour plus de solutions")
    print("="*60)


def read_cnk_list(input_file):
    """Lit la liste de CNK depuis le fichier d'entrée."""
    cnks = []
    with open(input_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip() and not row[0].strip().upper() == "CNK":
                cnks.append(row[0].strip())
    return cnks


def format_price_for_output(value):
    """Format a numeric price to string using comma as decimal separator.

    - Integers are written without decimals (e.g. 12)
    - Floats with fractional part are written with two decimals and comma (e.g. 12,40)
    - Non-numeric values ('' or 'NA') are returned as-is
    """
    if value is None:
        return ''
    # Already string 'NA' or empty
    if isinstance(value, str):
        return value
    try:
        v = float(value)
    except Exception:
        return str(value)

    if v.is_integer():
        return str(int(v))
    return f"{v:.2f}".replace('.', ',')


def read_grid_file(grid_file):
    """
    Lit le fichier grid avec noms, CNK et prix de base.
    Format attendu: Nom;CNK;Prix
    Retourne un tuple de 3 dictionnaires: (product_names, cnk_list, base_prices)
    """
    product_names = {}
    cnk_list = []
    base_prices = {}
    
    if not os.path.exists(grid_file):
        print(f"⚠️ Fichier grid '{grid_file}' non trouvé")
        return product_names, cnk_list, base_prices
    
    try:
        with open(grid_file, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if len(row) >= 3:
                    name = row[0].strip()
                    cnk = row[1].strip()
                    prix = row[2].strip()
                    if name and cnk:
                        product_names[cnk] = name
                        cnk_list.append(cnk)
                        base_prices[cnk] = prix
        print(f"📋 {len(product_names)} produits chargés depuis le fichier grid")
        print(f"  • {len(cnk_list)} CNKs")
        print(f"  • {len(base_prices)} prix de base")
    except Exception as e:
        print(f"⚠️ Erreur lors de la lecture du fichier grid: {e}")
    
    return product_names, cnk_list, base_prices


def scrape_medi_market(cnk_list):
    """Scrape Medi-Market pour une liste de CNK."""
    print("\n" + "="*60)
    print("🔵 PHASE 1: Scraping Medi-Market")
    print("="*60)
    
    from queue import Queue
    from threading import Thread, Lock
    
    PARAPHARMACIE_SITE = "https://medi-market.be/fr/search?q={cnk}"
    PHARMACIE_SITE = "https://pharmacy-medi-market.be/fr/search?q={cnk}"
    MAX_WORKERS = 10
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    ]
    
    def scrape_from_site(cnk, search_url):
        url = search_url.format(cnk=cnk)
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
        except:
            return None
        
        soup = BeautifulSoup(resp.content, "html.parser")
        star_div = soup.find("div", class_="skeepers_product__stars",
                           attrs={"data-product-id": str(cnk)})
        if not star_div:
            return None
        
        name_h2 = soup.find("h2", class_="text-base line-clamp-2 sm:line-clamp-3 md:group-hover:underline")
        if not name_h2:
            return None
        name = name_h2.get_text(strip=True)
        
        price_span = soup.find("span", class_=(
            "font-secondary text-[1.5rem]/[1.625rem] md:text-4xl "
            "text-right !leading-[42px] text-secondary"
        ))
        if not price_span:
            return None
        txt = price_span.get_text(strip=True).replace("€", "").replace("\xa0", "").replace(",", ".")
        try:
            price = float(txt)
        except:
            return None
        
        return [name, cnk, price]
    
    def worker(queue, site_url, results, counter, counter_lock, total, phase, processed_cnks, processed_lock):
        while True:
            try:
                cnk = queue.get(block=False)
            except:
                break
            
            with processed_lock:
                if cnk in processed_cnks:
                    queue.task_done()
                    continue
                processed_cnks.add(cnk)
            
            res = scrape_from_site(cnk, site_url)
            
            with counter_lock:
                counter[0] += 1
                idx = counter[0]
            
            if res:
                name, cnk, price = res
                print(f"✅ [{phase}] [{idx}/{total}] {name} – {price} €")
                results.append(res)
            else:
                print(f"❌ [{phase}] [{idx}/{total}] {cnk} non trouvé")
            
            queue.task_done()
    
    def run_phase(cnks, site_url, phase_name):
        if not cnks:
            return []
        
        q = Queue()
        for cnk in cnks:
            q.put(cnk)
        
        results = []
        counter = [0]
        counter_lock = Lock()
        processed_cnks = set()
        processed_lock = Lock()
        
        threads = []
        for _ in range(min(MAX_WORKERS, len(cnks))):
            t = Thread(
                target=worker,
                args=(q, site_url, results, counter, counter_lock, len(cnks), phase_name, processed_cnks, processed_lock),
                daemon=True,
            )
            t.start()
            threads.append(t)
        
        q.join()
        for t in threads:
            t.join()
        
        return results
    
    # Phase 1: Parapharmacie
    results_phase1 = run_phase(cnk_list, PARAPHARMACIE_SITE, "Parapharmacie")
    found_cnks = {r[1] for r in results_phase1}
    not_found = [cnk for cnk in cnk_list if cnk not in found_cnks]
    
    # Phase 2: Pharmacie (pour les non trouvés)
    results_phase2 = run_phase(not_found, PHARMACIE_SITE, "Pharmacie")
    
    all_results = results_phase1 + results_phase2
    
    # Créer dict CNK -> prix et CNK -> nom
    price_dict = {r[1]: r[2] for r in all_results}
    name_dict = {r[1]: r[0] for r in all_results}
    
    print(f"\n✅ Medi-Market: {len(price_dict)}/{len(cnk_list)} CNKs trouvés")
    return price_dict, name_dict


async def scrape_farmaline_async(cnk_list):
    """Scrape Farmaline avec anti-détection + cache intelligent de catégories."""
    print("\n" + "="*60)
    print("🟢 PHASE 2: Scraping Farmaline (anti-détection + cache intelligent)")
    print("="*60)
    
    import aiohttp
    from aiohttp_retry import RetryClient, ExponentialRetry
    
    BASE_URL = "https://www.farmaline.be"
    CONCURRENT = 2  # Très conservateur pour éviter le blocage
    
    # Cache intelligent : mémorise la catégorie du dernier produit trouvé
    # Format: {index_dans_liste: categorie}
    last_category_cache = {}
    
    # Cache par préfixe CNK (pour produits similaires)
    category_cache = {}
    
    # Compteur pour ajouter des pauses longues périodiques
    request_count = [0]
    
    async def scrape_product(client, cnk, cnk_index, categories, sem):
        async with sem:
            # Utiliser la rotation de headers réaliste
            headers = rotate_headers()
            headers["Referer"] = BASE_URL  # Ajouter referer pour plus de réalisme
            
            # OPTIMISATION INTELLIGENTE: Tester d'abord la catégorie du produit précédent
            # (souvent les produits consécutifs sont dans la même catégorie/gamme)
            priority_cats = []
            
            # 1. Catégorie du produit juste avant (index - 1)
            if cnk_index > 0 and (cnk_index - 1) in last_category_cache:
                prev_cat = last_category_cache[cnk_index - 1]
                priority_cats.append(prev_cat)
                print(f"🎯 Farmaline [{cnk}] Test catégorie du produit précédent: {prev_cat}")
            
            # 2. Catégorie des produits similaires (même préfixe CNK)
            if cnk[:3] in category_cache and category_cache[cnk[:3]] not in priority_cats:
                similar_cat = category_cache[cnk[:3]]
                priority_cats.append(similar_cat)
            
            # 3. Autres catégories (triées par longueur de nom = plus spécifiques d'abord)
            sorted_cats = sorted(categories, key=lambda c: (len(c), c))
            for cat in priority_cats:
                if cat in sorted_cats:
                    sorted_cats.remove(cat)
            
            # Catégories finales : prioritaires + autres
            final_cats = priority_cats + sorted_cats
            
            # Pause longue tous les 20 produits pour éviter la détection
            request_count[0] += 1
            if request_count[0] % 20 == 0:
                cooldown = random.uniform(10, 20)
                print(f"⏸️  Pause de sécurité ({cooldown:.1f}s) après {request_count[0]} requêtes...")
                await asyncio.sleep(cooldown)
            
            for idx, cat in enumerate(final_cats[:8]):  # Limiter à 8 catégories max
                url = f"{BASE_URL}/fr/{cat}/BE0{cnk}/"
                try:
                    # Utiliser délai humain réaliste
                    delay = human_like_delay()
                    if idx > 0:  # Délai plus long après la première tentative
                        delay += random.uniform(1, 2)
                    
                    await asyncio.sleep(delay)
                    
                    resp = await client.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15))
                    
                    # Tracker les erreurs de blocage
                    if resp.status == 403:
                        log_blocking_error('farmaline', 403)
                        print(f"⚠️ Farmaline [{cnk}] Erreur 403 - Blocage détecté")
                        return None
                    elif resp.status == 429:
                        log_blocking_error('farmaline', 429)
                        print(f"⚠️ Farmaline [{cnk}] Rate limit (429), pause de 60s...")
                        await asyncio.sleep(60)
                        continue
                    
                    if resp.status == 200:
                        html = await resp.text()
                        if "CNK" in html and "BE0" + cnk in html:  # Vérification plus stricte
                            soup = BeautifulSoup(html, "lxml")
                            h1 = soup.find("h1")
                            name = h1.get_text(strip=True) if h1 else "N/A"
                            
                            price_div = soup.find(
                                "div",
                                class_="text-xl font-bold text-dark-brand desktop:ml-3.5",
                                attrs={"data-qa-id": "product-page-variant-details__display-price"}
                            )
                            if price_div:
                                price_str = price_div.get_text(strip=True).replace("€","").replace("\xa0","").replace(",",".")
                                try:
                                    price = float(price_str)
                                    
                                    # 🎯 CACHE INTELLIGENT: Mémoriser la catégorie de CE produit
                                    last_category_cache[cnk_index] = cat
                                    category_cache[cnk[:3]] = cat
                                    
                                    if priority_cats and cat == priority_cats[0]:  # Si trouvé dans catégorie du produit précédent
                                        print(f"🎯✅ Farmaline [{cnk}] {name[:50]} – {price} € (catégorie précédente: {cat})")
                                    else:
                                        print(f"✅ Farmaline [{cnk}] {name[:50]} – {price} € (catégorie: {cat})")
                                    
                                    return cnk, name, price
                                except:
                                    pass
                        return cnk, None, None
                    elif resp.status == 403:  # Forbidden
                        print(f"⚠️ Accès bloqué (403), pause de 60s...")
                        await asyncio.sleep(60)
                        return cnk, None, None
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    if "429" in str(e) or "403" in str(e):
                        print(f"⚠️ Blocage détecté, pause de 60s...")
                        await asyncio.sleep(60)
                        return cnk, None, None
                    continue
            
            print(f"❌ Farmaline [{cnk}] non trouvé")
            return cnk, None, None
    
    async def get_categories(client):
        """Récupère les catégories simples avec cache."""
        try:
            # Utiliser rotation de headers
            headers = rotate_headers()
            resp = await client.get(f"{BASE_URL}/fr/", headers=headers, timeout=aiohttp.ClientTimeout(total=15))
            html = await resp.text()
            soup = BeautifulSoup(html, "lxml")
            nav = soup.select_one("div.relative.flex.size-full.flex-col")
            cats = []
            if nav:
                for li in nav.find_all("li", class_="relative font-bold"):
                    a = li.find("a")
                    href = a.get("href","") if a else ""
                    if href.startswith("/fr/"):
                        cat = href.split("/")[2]
                        if cat not in cats and cat:
                            cats.append(cat)
            return cats[:12] if len(cats) > 12 else cats  # Limiter aux 12 premières
        except:
            # Fallback : catégories hardcodées courantes
            return ["sante", "bebe-maman", "beaute", "complement-alimentaire", "hygiene", "medicament"]
    
    # Créer session avec timeouts optimisés et headers réalistes
    retry_options = ExponentialRetry(attempts=2, start_timeout=2, factor=2.0)
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    connector = aiohttp.TCPConnector(limit=CONCURRENT, ssl=False, force_close=False)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        retry_client = RetryClient(client_session=session, retry_options=retry_options, raise_for_status=False)
        
        categories = await get_categories(retry_client)
        print(f"📚 {len(categories)} catégories Farmaline détectées")
        
        sem = asyncio.Semaphore(CONCURRENT)
        tasks = [scrape_product(retry_client, cnk, idx, categories, sem) for idx, cnk in enumerate(cnk_list)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filtrer les exceptions et extraire les noms
    valid_results = []
    names_dict = {}
    for r in results:
        if isinstance(r, tuple) and len(r) == 3:
            cnk, name, price = r
            valid_results.append((cnk, price))
            if name:
                names_dict[cnk] = name
        elif isinstance(r, Exception):
            print(f"⚠️ Erreur capturée: {r}")
    
    # Créer dict CNK -> prix
    price_dict = {cnk: price for cnk, price in valid_results if price is not None}
    
    print(f"\n✅ Farmaline: {len(price_dict)}/{len(cnk_list)} CNKs trouvés")
    return price_dict, names_dict


def scrape_newpharma(cnk_list, product_names, medi_names=None):
    """Scrape NewPharma avec cloudscraper pour contourner Cloudflare.
    
    Compare la qualité du match avec :
    1. Le nom d'input (product_names)
    2. Le nom trouvé sur Medi-Market (medi_names) - optionnel
    
    Retourne les scores les plus élevés entre les deux sources.
    """
    print("\n" + "="*60)
    print("🟡 PHASE 3: Scraping NewPharma (cloudscraper + anti-Cloudflare)")
    print("="*60)
    
    if medi_names is None:
        medi_names = {}
    
    # Ouvrir fichier de logging
    LOG_FILE = "/tmp/newpharma.log"
    with open(LOG_FILE, "w") as f:
        f.write(f"=== NewPharma Scraping Log === {datetime.now().isoformat()}\n\n")
    
    def log_to_file(message):
        """Écrire dans le fichier log et afficher en console."""
        with open(LOG_FILE, "a") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
    
    log_to_file("🟡 Démarrage du scraping NewPharma")
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # Importer cloudscraper pour contourner Cloudflare
    try:
        import cloudscraper
        print("✅ cloudscraper chargé - Cloudflare bypass activé")
    except ImportError:
        print("❌ cloudscraper non installé - Installation requise:")
        print("   pip install cloudscraper")
        return {}, {}
    
    # Importer rapidfuzz pour le calcul de similarité
    try:
        from rapidfuzz import fuzz
    except ImportError:
        print("⚠️ rapidfuzz non installé, utilisation de matching simple")
        class fuzz:
            @staticmethod
            def ratio(a, b):
                a_clean = a.lower().strip()
                b_clean = b.lower().strip()
                if a_clean == b_clean:
                    return 100
                if a_clean in b_clean or b_clean in a_clean:
                    return 85
                # Compter les mots en commun
                words_a = set(a_clean.split())
                words_b = set(b_clean.split())
                common = len(words_a & words_b)
                total = len(words_a | words_b)
                return (common / total * 100) if total > 0 else 0
    
    # Créer un scraper cloudscraper qui contourne automatiquement Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    MAX_WORKERS = 2  # Très conservateur pour éviter le blocage
    
    def search_product(cnk, product_name, medi_name, retry=0):
        """Recherche un produit par nom sur NewPharma.
        
        Fait un matching fuzzy contre :
        - product_name (nom d'input)
        - medi_name (nom trouvé sur Medi-Market)
        
        Retourne le meilleur score des deux sources.
        """
        if not product_name or product_name.upper() == "NA":
            log_to_file(f"[{cnk}] Nom de produit vide ou NA")
            return cnk, None, None, 0
        
        try:
            # Utiliser délai humain réaliste
            delay = human_like_delay()
            log_to_file(f"[{cnk}] Délai anti-détection: {delay:.2f}s")
            time.sleep(delay)
            
            # Rotation de headers pour chaque requête
            headers = rotate_headers()
            headers["Referer"] = "https://www.newpharma.be/"
            
            q = quote_plus(product_name)
            url = f"https://www.newpharma.be/fr/search-results/search.html?q={q}"
            
            log_to_file(f"[{cnk}] Recherche: {product_name}")
            if medi_name and medi_name != "NA":
                log_to_file(f"[{cnk}]   (Medi-Market source: {medi_name})")
            log_to_file(f"[{cnk}] URL: {url}")
            log_to_file(f"[{cnk}] User-Agent: {headers.get('User-Agent', 'N/A')[:60]}...")
            
            # Utiliser cloudscraper au lieu de session.get
            resp = scraper.get(url, headers=headers, timeout=30)
            
            log_to_file(f"[{cnk}] Réponse: Status {resp.status_code} ({len(resp.content)} bytes)")
            
            # Tracker les erreurs de blocage
            if resp.status_code == 403:
                log_blocking_error('newpharma', 403)
                log_to_file(f"[{cnk}] ⚠️ Erreur 403 Forbidden (tentative {retry})")
                if retry < 2:
                    print(f"⚠️ NewPharma [{cnk}] Erreur 403, pause de 60s avant retry...")
                    time.sleep(60)
                    return search_product(cnk, product_name, medi_name, retry + 1)
                else:
                    log_to_file(f"[{cnk}] ❌ Bloqué (403) après {retry} tentatives")
                    print(f"⚠️ NewPharma [{cnk}] Bloqué (403) après {retry} tentatives")
                    return cnk, None, None, 0
            
            if resp.status_code == 429:
                log_blocking_error('newpharma', 429)
                log_to_file(f"[{cnk}] ⚠️ Rate limit (429) (tentative {retry})")
                if retry < 3:
                    print(f"⚠️ NewPharma [{cnk}] Rate limit (429), pause de 90s...")
                    time.sleep(90)
                    return search_product(cnk, product_name, medi_name, retry + 1)
                else:
                    log_to_file(f"[{cnk}] ❌ Rate limit persistant après {retry} tentatives")
                    print(f"⚠️ NewPharma [{cnk}] Rate limit persistant après {retry} tentatives")
                    return cnk, None, None, 0
            
            if resp.status_code != 200:
                log_to_file(f"[{cnk}] ❌ Status HTTP {resp.status_code}")
                return cnk, None, None, 0
            
            soup = BeautifulSoup(resp.content, "lxml")
            divs = soup.find_all("div", attrs={"data-google-360": True})
            
            log_to_file(f"[{cnk}] ✅ Trouvé {len(divs)} produits candidats")
            
            if not divs:
                log_to_file(f"[{cnk}] ❌ Aucun produit trouvé")
                return cnk, None, None, 0
            
            best_match_price = None
            best_score = 0
            best_name = None
            best_source = None
            
            for idx, div in enumerate(divs):
                raw = div.get("data-google-360", "")
                try:
                    data = json.loads(raw.replace("&quot;", '"'))
                    items = data.get("ecommerce", {}).get("items", [])
                except:
                    continue
                
                for item in items:
                    item_name = item.get("item_name")
                    price = item.get("price")
                    if not item_name or price is None:
                        continue
                    
                    # Comparer contre le nom d'input
                    score_input = fuzz.ratio(product_name.lower(), item_name.lower())
                    
                    # Comparer contre le nom Medi-Market si disponible
                    score_medi = 0
                    source = "grid"
                    if medi_name and medi_name != "NA":
                        score_medi = fuzz.ratio(medi_name.lower(), item_name.lower())
                        if score_medi > score_input:
                            score_input = score_medi
                            source = "medi-market"
                    
                    log_to_file(f"[{cnk}]   Candidat #{idx}: {item_name[:50]}...")
                    log_to_file(f"[{cnk}]      Prix: {price}€ | Score (grid): {score_input:.0f}%" + (f" | Score (Medi): {score_medi:.0f}%" if medi_name and medi_name != "NA" else ""))
                    
                    if score_input > best_score:
                        best_score = score_input
                        best_match_price = price
                        best_name = item_name
                        best_source = source
                    
                    # Si score parfait, pas besoin de chercher plus
                    if score_input >= 98:
                        break
                
                if best_score >= 98:
                    break
            
            if best_match_price is not None:
                # Afficher avec indicateur de fiabilité
                if best_score >= 90:
                    indicator = "✅"
                elif best_score >= 70:
                    indicator = "⚠️"
                else:
                    indicator = "❓"
                
                source_indicator = f" (src: {best_source})" if best_source else ""
                log_to_file(f"[{cnk}] {indicator} MEILLEUR MATCH: {best_name[:50]}... → {best_match_price}€ (score: {best_score:.0f}%){source_indicator}")
                print(f"{indicator} NewPharma [{cnk}] {product_name[:40]}... – {best_match_price} € (match: {best_score:.0f}%{source_indicator})")
                return cnk, str(best_match_price), best_name, best_score
            
            log_to_file(f"[{cnk}] ❌ Aucun match acceptable trouvé")
            return cnk, None, None, 0
            
        except Exception as e:
            log_to_file(f"[{cnk}] ❌ Exception: {type(e).__name__}: {str(e)[:100]}")
            print(f"❌ NewPharma [{cnk}] Erreur: {type(e).__name__}")
            return cnk, None, None, 0
    
    # Préparer les tâches
    tasks = []
    for cnk in cnk_list:
        name = product_names.get(cnk)
        if name:
            medi_name = medi_names.get(cnk)  # Peut être None
            tasks.append((cnk, name, medi_name))
    
    if not tasks:
        print("⚠️ Aucun nom de produit disponible pour NewPharma")
        return {}, {}
    
    print(f"🔍 {len(tasks)} CNK avec noms disponibles pour NewPharma")
    
    results = {}
    match_scores = {}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(search_product, cnk, name, medi_name): cnk for cnk, name, medi_name in tasks}
        
        completed = 0
        for future in as_completed(futures):
            cnk, price, found_name, match_score = future.result()
            if price:
                results[cnk] = price
                match_scores[cnk] = match_score
            completed += 1
            
            # Pause tous les 10 produits
            if completed % 10 == 0 and completed < len(tasks):
                pause = random.uniform(10, 20)
                print(f"⏸️  Pause de sécurité ({pause:.1f}s)...")
                time.sleep(pause)
    
    # Statistiques sur les scores de match
    if match_scores:
        avg_score = sum(match_scores.values()) / len(match_scores)
        high_quality = sum(1 for s in match_scores.values() if s >= 90)
        medium_quality = sum(1 for s in match_scores.values() if 70 <= s < 90)
        low_quality = sum(1 for s in match_scores.values() if s < 70)
        
        print(f"\n📊 Qualité des correspondances NewPharma:")
        print(f"  • Score moyen: {avg_score:.1f}%")
        print(f"  • Haute qualité (≥90%): {high_quality}")
        print(f"  • Qualité moyenne (70-89%): {medium_quality}")
        print(f"  • Qualité faible (<70%): {low_quality}")
    
    print(f"\n✅ NewPharma: {len(results)}/{len(cnk_list)} CNKs trouvés")
    return results, match_scores


def scrape_multipharma(cnk_list, product_names_grid, product_names_medi):
    """Scrape Multipharma en recherchant par nom de produit (grid et medi-market) - VERSION ASYNC."""
    print("\n" + "="*60)
    print("🟣 PHASE 4: Scraping Multipharma (ASYNC)")
    print("="*60)
    
    import asyncio
    import aiohttp
    import re
    from collections import deque
    
    # Importer rapidfuzz pour le calcul de similarité
    try:
        from rapidfuzz import fuzz
    except ImportError:
        print("⚠️ rapidfuzz non installé, utilisation de matching simple")
        class fuzz:
            @staticmethod
            def ratio(a, b):
                a_clean = a.lower().strip()
                b_clean = b.lower().strip()
                if a_clean == b_clean:
                    return 100
                if a_clean in b_clean or b_clean in a_clean:
                    return 85
                # Compter les mots en commun
                words_a = set(a_clean.split())
                words_b = set(b_clean.split())
                common = len(words_a & words_b)
                total = len(words_a | words_b)
                return (common / total * 100) if total > 0 else 0
    
    BASE_URL = "https://www.multipharma.be"
    SEARCH_URL = f"{BASE_URL}/on/demandware.store/Sites-Multipharma-Webshop-BE-Site/fr_BE/Search-Show?q="
    
    # Configuration adaptive
    INITIAL_WORKERS = 10  # Démarrage progressif
    MAX_WORKERS = 30      # Monter jusqu'à 30 si tout va bien
    RAMP_UP_STEP = 5      # Augmenter de 5 workers toutes les 10 requêtes réussies
    MIN_DELAY = 0.1       # Délai minimum très court
    MAX_DELAY = 0.5       # Délai maximum réduit
    ADAPTIVE_WINDOW = 20  # Fenêtre pour calcul des stats (dernières N requêtes)
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    # Classe pour gérer les délais adaptatifs
    class AdaptiveDelayManager:
        def __init__(self):
            self.response_times = deque(maxlen=ADAPTIVE_WINDOW)
            self.error_count = 0
            self.success_count = 0
            self.current_delay = MIN_DELAY
            self.current_workers = INITIAL_WORKERS
        
        def record_success(self, response_time):
            self.response_times.append(response_time)
            self.success_count += 1
            # Si tout va bien, réduire les délais et augmenter workers
            if self.success_count % 10 == 0 and self.current_delay > MIN_DELAY:
                self.current_delay = max(MIN_DELAY, self.current_delay * 0.9)
            if self.success_count % 10 == 0 and self.current_workers < MAX_WORKERS:
                self.current_workers = min(MAX_WORKERS, self.current_workers + RAMP_UP_STEP)
        
        def record_error(self, error_code):
            self.error_count += 1
            # Si erreurs, augmenter délais et réduire workers
            if error_code in [429, 403]:
                self.current_delay = min(MAX_DELAY * 2, self.current_delay * 1.5)
                self.current_workers = max(5, self.current_workers - RAMP_UP_STEP)
        
        def get_delay(self):
            # Retourner un délai aléatoire dans la plage adaptée
            return random.uniform(self.current_delay, self.current_delay * 2)
    
    delay_manager = AdaptiveDelayManager()
    
    async def search_product(session, cnk, product_name, retry=0):
        """Recherche un produit par nom sur Multipharma (async)."""
        if not product_name or product_name.upper() == "NA":
            return cnk, None, None, 0
        
        try:
            encoded_name = quote_plus(product_name)
            search_url = f"{SEARCH_URL}{encoded_name}"
            
            # Délai adaptatif
            await asyncio.sleep(delay_manager.get_delay())
            
            start_time = time.time()
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response_time = time.time() - start_time
                
                if response.status == 429 and retry < 3:
                    delay_manager.record_error(429)
                    await asyncio.sleep(random.uniform(30, 60))
                    return await search_product(session, cnk, product_name, retry + 1)
                
                if response.status == 403 and retry < 2:
                    delay_manager.record_error(403)
                    await asyncio.sleep(random.uniform(20, 40))
                    return await search_product(session, cnk, product_name, retry + 1)
                
                if response.status != 200:
                    return cnk, None, None, 0
                
                html_content = await response.text()
                delay_manager.record_success(response_time)
            
            soup = BeautifulSoup(html_content, "lxml")
            
            # Chercher le premier produit
            product = None
            selectors = [
                "div.product-tile",
                "div.product",
                "div[class*='product']",
                "article.product",
                "li.product-tile",
            ]
            
            for selector in selectors:
                products = soup.select(selector)
                if products:
                    product = products[0]
                    break
            
            # Vérifier si redirection directe vers page produit
            if not product:
                product_page_indicators = [
                    "div.product-detail",
                    "div.product-info",
                    "div[class*='product-detail']",
                ]
                for indicator in product_page_indicators:
                    if soup.select(indicator):
                        product = soup
                        break
            
            if not product:
                return cnk, None, None, 0
            
            # Chercher le nom du produit trouvé
            found_name = None
            name_selectors = [
                "div.pdp-link",
                "a.product-tile-title",
                "h1.product-name",
                "h2.product-name",
                "div.product-name",
                "a[class*='product-name']",
                "h1",
                "h2",
            ]
            
            for selector in name_selectors:
                name_elem = product.select_one(selector)
                if name_elem:
                    found_name = name_elem.get_text(strip=True)
                    if found_name and len(found_name) > 5:  # Nom valide
                        break
            
            # Calculer le score de correspondance
            match_score = 0
            if found_name:
                match_score = fuzz.ratio(product_name.lower(), found_name.lower())
            
            # Chercher le prix
            price_selectors = [
                "div.sales",
                "span.sales",
                "div.price",
                "span.price",
                "span.price-sales",
                "div.price span.value",
                "span[class*='price']",
                "div[class*='price']",
            ]
            
            for selector in price_selectors:
                price_elem = product.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_text = price_text.replace("€", "").replace(",", ".").strip()
                    match = re.search(r"(\d+\.?\d*)", price_text)
                    if match:
                        price = match.group(1)
                        
                        # Afficher avec indicateur de fiabilité
                        if match_score >= 90:
                            indicator = "✅"
                        elif match_score >= 70:
                            indicator = "⚠️"
                        else:
                            indicator = "❓"
                        
                        print(f"{indicator} Multipharma [{cnk}] {product_name[:40]}... – {price} € (match: {match_score:.0f}%)")
                        return cnk, price, found_name, match_score
            
            return cnk, None, None, 0
            
        except asyncio.TimeoutError:
            print(f"⏱️ Multipharma [{cnk}] Timeout")
            return cnk, None, None, 0
        except Exception as e:
            print(f"❌ Multipharma [{cnk}] Erreur: {type(e).__name__}")
            return cnk, None, None, 0
    
    # Préparer les tâches avec les deux sources de noms
    tasks = []
    for cnk in cnk_list:
        name_grid = product_names_grid.get(cnk)
        name_medi = product_names_medi.get(cnk)
        # On a besoin d'au moins un nom pour chercher
        if name_grid or name_medi:
            tasks.append((cnk, name_grid, name_medi))
    
    if not tasks:
        print("⚠️ Aucun nom de produit disponible pour Multipharma")
        return {}, {}, {}
    
    print(f"🔍 {len(tasks)} CNK avec noms disponibles pour Multipharma")
    
    results = {}
    match_scores = {}  # Stocker les scores de correspondance
    match_sources = {}  # Stocker la source du meilleur match (Grid ou MediMarket)
    
    async def process_all_products():
        """Traite tous les produits de manière asynchrone."""
        # Configuration du connecteur avec pool de connexions
        connector = aiohttp.TCPConnector(
            limit=50,  # Nombre max de connexions simultanées
            limit_per_host=30,  # Par host
            ttl_dns_cache=300
        )
        
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        
        async with aiohttp.ClientSession(
            headers=HEADERS,
            connector=connector,
            timeout=timeout
        ) as session:
            
            completed = 0
            semaphore = asyncio.Semaphore(delay_manager.current_workers)
            
            async def process_product_with_semaphore(cnk, name_grid, name_medi):
                """Traite un produit avec limitation de concurrence."""
                async with semaphore:
                    # Chercher avec le nom du grid
                    best_price = None
                    best_score = 0
                    best_source = None
                    best_found_name = None
                    
                    if name_grid:
                        cnk_result, price, found_name, match_score = await search_product(session, cnk, name_grid)
                        if price and match_score > best_score:
                            best_price = price
                            best_score = match_score
                            best_source = "Fichier Source"
                            best_found_name = found_name
                    
                    # Chercher avec le nom trouvé sur Medi-Market
                    if name_medi:
                        cnk_result, price, found_name, match_score = await search_product(session, cnk, name_medi)
                        if price and match_score > best_score:
                            best_price = price
                            best_score = match_score
                            best_source = "MediMarket"
                            best_found_name = found_name
                    
                    # Garder le meilleur résultat
                    if best_price:
                        results[cnk] = best_price
                        match_scores[cnk] = best_score
                        match_sources[cnk] = best_source
                    
                    return cnk
            
            # Traiter par batches pour le ramp-up progressif
            batch_size = 10
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                batch_tasks = [
                    process_product_with_semaphore(cnk, name_grid, name_medi)
                    for cnk, name_grid, name_medi in batch
                ]
                
                # Attendre que le batch soit terminé
                await asyncio.gather(*batch_tasks, return_exceptions=True)
                completed += len(batch)
                
                # Ajuster dynamiquement le semaphore
                semaphore = asyncio.Semaphore(delay_manager.current_workers)
                
                # Pause périodique pour éviter la détection
                if completed % 50 == 0 and completed < len(tasks):
                    pause = random.uniform(1, 2)
                    print(f"⏸️  Pause de sécurité ({pause:.1f}s) - Workers: {delay_manager.current_workers}, Delay: {delay_manager.current_delay:.2f}s")
                    await asyncio.sleep(pause)
    
    # Exécuter la boucle async
    asyncio.run(process_all_products())
    
    # Statistiques sur les scores de match
    if match_scores:
        avg_score = sum(match_scores.values()) / len(match_scores)
        high_quality = sum(1 for s in match_scores.values() if s >= 90)
        medium_quality = sum(1 for s in match_scores.values() if 70 <= s < 90)
        low_quality = sum(1 for s in match_scores.values() if s < 70)
        
        # Statistiques sur les sources
        grid_count = sum(1 for s in match_sources.values() if s == "Fichier Source")
        medi_count = sum(1 for s in match_sources.values() if s == "MediMarket")
        
        print(f"\n📊 Qualité des correspondances Multipharma:")
        print(f"  • Score moyen: {avg_score:.1f}%")
        print(f"  • Haute qualité (≥90%): {high_quality}")
        print(f"  • Qualité moyenne (70-89%): {medium_quality}")
        print(f"  • Qualité faible (<70%): {low_quality}")
        print(f"\n📍 Sources des meilleurs matchs:")
        print(f"  • Fichier Source: {grid_count}")
        print(f"  • Nom MediMarket: {medi_count}")
    
    print(f"\n✅ Multipharma: {len(results)}/{len(cnk_list)} CNKs trouvés")
    return results, match_scores, match_sources


def consolidate_results(cnk_list, product_names, base_prices, medi_prices, medi_names, multipharma_prices, multipharma_scores, multipharma_sources, newpharma_prices, newpharma_scores, output_file):
    """Fusionne les résultats des 3 sites dans un CSV unique."""
    print("\n" + "="*60)
    print("📊 CONSOLIDATION des résultats")
    print("="*60)
    
    rows = []
    for cnk in cnk_list:
        name = product_names.get(cnk, "")
        base_price = base_prices.get(cnk, "NA")
        medi_price = medi_prices.get(cnk, "NA")
        multi_price = multipharma_prices.get(cnk, "NA")
        newp_price = newpharma_prices.get(cnk, "NA")
        
        # Scores de match (Medi-Market cherche par CNK donc toujours 100% si trouvé)
        medi_score = "100%" if medi_price != "NA" else ""
        
        multi_score = multipharma_scores.get(cnk, "")
        multi_score_str = f"{multi_score:.0f}%" if multi_score else ""
        
        multi_source = multipharma_sources.get(cnk, "")
        
        newp_score = newpharma_scores.get(cnk, "")
        newp_score_str = f"{newp_score:.0f}%" if newp_score else ""
        
        # Format numeric prices for CSV output using comma as decimal separator
        rows.append([
            name,
            cnk,
            format_price_for_output(base_price),
            format_price_for_output(medi_price),
            format_price_for_output(multi_price),
            format_price_for_output(newp_price),
            medi_score,
            multi_score_str,
            multi_source,
            newp_score_str
        ])
    
    # Écrire le CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Nom_Produit", 
            "CNK", 
            "Prix_Base", 
            "Prix_MediMarket", 
            "Prix_Multipharma", 
            "Prix_NewPharma",
            "Match_MediMarket",
            "Match_Multipharma",
            "Match_Source_Multipharma",
            "Match_NewPharma"
        ])
        writer.writerows(rows)
    
    # Statistiques
    stats = {
        "total": len(cnk_list),
        "medi": sum(1 for row in rows if row[3] != "NA"),
        "multipharma": sum(1 for row in rows if row[4] != "NA"),
        "newpharma": sum(1 for row in rows if row[5] != "NA"),
    }
    
    print(f"\n📈 Statistiques de couverture:")
    print(f"  • Total CNK: {stats['total']}")
    print(f"  • Medi-Market: {stats['medi']} ({stats['medi']/stats['total']*100:.1f}%)")
    print(f"  • Multipharma: {stats['multipharma']} ({stats['multipharma']/stats['total']*100:.1f}%)")
    print(f"  • NewPharma: {stats['newpharma']} ({stats['newpharma']/stats['total']*100:.1f}%)")
    print(f"\n📦 Résultats consolidés → {output_file}")


def main():
    # Support -h/--help
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Usage:")
        print("  Mode fichier CSV:")
        print("    python src/scraper.py [grid_file] [output_file]")
        print("    python src/scraper.py --run")
        print("")
        print("  Mode Google Sheets:")
        print("    python src/scraper.py --sheet <sheet_name>")
        print("")
        print("Exemples:")
        print("  python src/scraper.py data/input/grid.csv data/output/resultats.csv")
        print("  python src/scraper.py --sheet test_pharma_scrap")
        sys.exit(0)

    # Defaults: data/input/grid.csv and timestamped output in data/output/
    project_root = Path(__file__).parents[1]
    default_input = project_root / "data" / "input" / "grid.csv"
    default_output = project_root / "data" / "output" / f"resultats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    # Check for --sheet mode
    sheet_mode = False
    sheet_name = None
    creds_path_arg = None
    limit_arg = None
    if "--sheet" in sys.argv:
        sheet_mode = True
        sheet_idx = sys.argv.index("--sheet")
        if sheet_idx + 1 < len(sys.argv) and not sys.argv[sheet_idx + 1].startswith("--"):
            sheet_name = sys.argv[sheet_idx + 1]
        else:
            print("❌ Erreur: --sheet nécessite un nom de Google Sheet")
            print("Exemple: python src/scraper.py --sheet test_pharma_scrap")
            sys.exit(1)

    # Optional: explicit credentials file path
    if "--creds" in sys.argv:
        creds_idx = sys.argv.index("--creds")
        if creds_idx + 1 < len(sys.argv) and not sys.argv[creds_idx + 1].startswith("--"):
            creds_path_arg = sys.argv[creds_idx + 1]
        else:
            print("❌ Erreur: --creds nécessite un chemin vers le fichier JSON des credentials")
            sys.exit(1)

    # Optional: limit number of CNKs to process (for quick tests)
    if "--limit" in sys.argv:
        limit_idx = sys.argv.index("--limit")
        if limit_idx + 1 < len(sys.argv) and not sys.argv[limit_idx + 1].startswith("--"):
            try:
                limit_arg = int(sys.argv[limit_idx + 1])
            except ValueError:
                print("❌ Erreur: --limit nécessite un entier")
                sys.exit(1)
        else:
            print("❌ Erreur: --limit nécessite un entier (ex: --limit 5)")
            sys.exit(1)

    if sheet_mode:
        # Mode Google Sheets
        print("="*60)
        print("🚀 MASTER SCRAPER - Mode Google Sheets")
        print("="*60)
        print(f"📊 Google Sheet: {sheet_name}")
        print(f"📋 Onglet: resultats_final")
        
        # Import du module Google Sheets
        try:
            # Add src directory to path if not already there
            src_dir = Path(__file__).parent
            if str(src_dir) not in sys.path:
                sys.path.insert(0, str(src_dir))
            
            import google_sheets
        except ImportError as e:
            print(f"\n❌ Erreur: module google_sheets introuvable: {e}")
            print("Installez les dépendances: pip install -r requirements.txt")
            sys.exit(1)
        
        start_time = time.time()
        
        # Ouvrir la Google Sheet
        try:
            # Pass explicit creds path when provided, otherwise google_sheets will fall back to env or default
            spreadsheet = google_sheets.open_sheet(sheet_name, creds_path=creds_path_arg)
        except Exception as e:
            print(f"\n❌ Erreur lors de l'ouverture de la Google Sheet: {e}")
            sys.exit(1)
        
        # Lire les CNK et les noms (colonne Nom_Produit) depuis la feuille
        try:
            cnk_list, cnk_to_row, cnk_to_name = google_sheets.read_cnks(
                spreadsheet,
                worksheet_name='resultats_final',
                cnk_col='CNK',
                name_col='Nom_Produit'
            )
        except Exception as e:
            print(f"\n❌ Erreur lors de la lecture des CNK: {e}")
            sys.exit(1)
        
        # Appliquer un limit si demandé
        if limit_arg is not None:
            cnk_list = cnk_list[:limit_arg]
            # Rebuild cnk_to_row mapping for subset
            cnk_to_row = {cnk: cnk_to_row[cnk] for cnk in cnk_list}

        # Pour Google Sheets, lire les noms de produit fournis dans la colonne 'Nom_Produit'
        # (colonne A) et les utiliser comme source 'Grid' pour le fuzzy matching.
        # read_cnks retourne maintenant (cnk_list, cnk_to_row, cnk_to_name)
        # Use the names read from the sheet
        product_names = cnk_to_name

        base_prices = {cnk: "" for cnk in cnk_list}
        
        print(f"\n🔍 {len(cnk_list)} CNKs à traiter")
        
        # Phase 1: Scrape Medi-Market (retourne prix et noms)
        medi_prices, medi_names = scrape_medi_market(cnk_list)
        
        # Phase 2: Scrape Farmaline (avec anti-détection) 🆕
        farmaline_prices, farmaline_names = asyncio.run(scrape_farmaline_async(cnk_list))
        
        # Phase 3: Scrape NewPharma (avec anti-détection) 🆕
        newpharma_prices, newpharma_scores = scrape_newpharma(cnk_list, product_names, medi_names)
        
        # Phase 4: Scrape Multipharma avec les noms trouvés sur Medi-Market
        multipharma_prices, multipharma_scores, multipharma_sources = scrape_multipharma(
            cnk_list, product_names, medi_names
        )
        
        # Préparer les résultats pour Google Sheets
        print("\n" + "="*60)
        print("📊 PRÉPARATION des résultats pour Google Sheets")
        print("="*60)
        
        def to_numeric(value):
            """Convertit une valeur en float pour Google Sheets, ou retourne ''."""
            if not value or value == "NA":
                return ''
            try:
                # Si c'est déjà un nombre, le retourner
                if isinstance(value, (int, float)):
                    return float(value)
                # Si c'est une string, la convertir
                return float(str(value).replace(',', '.'))
            except (ValueError, AttributeError):
                return ''
        
        results = {}
        for cnk in cnk_list:
            source_val = multipharma_sources.get(cnk, '')
            # Write source directly without "Source : " prefix
            formatted_source = source_val if source_val else ''
            
            # Convertir les prix et scores en numériques
            medi_price = to_numeric(medi_prices.get(cnk, ''))
            farma_price = to_numeric(farmaline_prices.get(cnk, ''))
            newp_price = to_numeric(newpharma_prices.get(cnk, ''))
            multi_price = to_numeric(multipharma_prices.get(cnk, ''))
            
            multi_score = multipharma_scores.get(cnk, '')
            newp_score = newpharma_scores.get(cnk, '')
            
            # Convertir les scores de pourcentage (0-100) en décimal (0-1)
            if multi_score:
                try:
                    multi_score = float(multi_score) / 100.0
                except (ValueError, TypeError):
                    multi_score = ''
            
            if newp_score:
                try:
                    newp_score = float(newp_score) / 100.0
                except (ValueError, TypeError):
                    newp_score = ''
            
            results[cnk] = {
                'Prix_MediMarket': medi_price,
                'Prix_Farmaline': farma_price,
                'Prix_NewPharma': newp_price,
                'Prix_Multipharma': multi_price,
                'Match_Multipharma': multi_score if multi_score else '',  # Score en décimal (0-1)
                'Match_NewPharma': newp_score if newp_score else '',  # Score en décimal (0-1)
                'Match_Source_Multipharma': formatted_source,
            }
        
        # Calculer Prix Moyen et Prix Min
        results = google_sheets.calculate_stats(results)
        
        # Écrire dans Google Sheets
        try:
            google_sheets.write_results(
                spreadsheet,
                worksheet_name='resultats_final',
                cnk_to_row=cnk_to_row,
                results=results
            )
        except Exception as e:
            print(f"\n❌ Erreur lors de l'écriture dans Google Sheets: {e}")
            sys.exit(1)
        
        # Afficher le rapport de blocage
        print_blocking_report()
        
        elapsed = time.time() - start_time
        print(f"\n⏱️ Temps total d'exécution: {elapsed:.2f}s ({elapsed/60:.2f} min)")
        print(f"\n✅ Scraping terminé et résultats écrits dans Google Sheet!")
        print(f"🔗 URL: {spreadsheet.url}")
        
        return
    
    # Mode fichier CSV (comportement original)
    run_flag = "--run" in sys.argv
    # Collect positional args (ignore flags like --run, --sheet, etc.)
    pos_args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if len(pos_args) == 0:
        # No positional args: show defaults and exit unless --run is provided
        print("\n⚠️  Aucun fichier d'entrée fourni. Valeurs par défaut proposées:")
        print(f"  • Input (par défaut): {default_input}")
        print(f"  • Output (par défaut): {default_output}")
        print("\nPour lancer le scraper avec ces valeurs, relancez avec --run:\n  python src/scraper.py --run\nou utilisez le script ./run_scraper.sh\n")
        if run_flag:
            grid_file = str(default_input)
            output_file = str(default_output)
        else:
            sys.exit(0)
    elif len(pos_args) == 1:
        grid_file = pos_args[0]
        output_file = str(default_output)
    else:
        grid_file = pos_args[0]
        output_file = pos_args[1]
    
    # Vérifier que le fichier grid existe
    if not os.path.exists(grid_file):
        print(f"❌ Erreur: fichier grid '{grid_file}' introuvable")
        sys.exit(1)
    
    print("="*60)
    print("🚀 MASTER SCRAPER - 2 Sites Pharma")
    print("="*60)
    print(f"📋 Grid file: {grid_file}")
    print(f"📁 Output: {output_file}")
    
    start_time = time.time()
    
    # Lire les données depuis le fichier grid
    product_names, cnk_list, base_prices = read_grid_file(grid_file)
    
    if not cnk_list:
        print("❌ Aucun CNK trouvé dans le fichier grid")
        sys.exit(1)
    
    print(f"\n🔍 {len(cnk_list)} CNKs à traiter")
    
    # Phase 1: Scrape Medi-Market (retourne prix et noms)
    medi_prices, medi_names = scrape_medi_market(cnk_list)
    
    # Phase 2: Scrape Multipharma avec les noms du grid ET les noms trouvés sur Medi-Market
    multipharma_prices, multipharma_scores, multipharma_sources = scrape_multipharma(cnk_list, product_names, medi_names)
    
    # NewPharma désactivé (bloque les requêtes avec 403)
    newpharma_prices = {}
    newpharma_scores = {}
    
    # Consolidation finale
    consolidate_results(
        cnk_list, 
        product_names, 
        base_prices, 
        medi_prices,
        medi_names,
        multipharma_prices, 
        multipharma_scores,
        multipharma_sources,
        newpharma_prices,
        newpharma_scores,
        output_file
    )
    
    elapsed = time.time() - start_time
    print(f"\n⏱️ Temps total d'exécution: {elapsed:.2f}s ({elapsed/60:.2f} min)")
    print("\n✅ Scraping terminé avec succès!")


if __name__ == "__main__":
    main()

