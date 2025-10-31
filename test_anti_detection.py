#!/usr/bin/env python3
"""
Script de test pour vérifier que l'anti-détection fonctionne sur Farmaline et NewPharma.
Test avec un seul CNK pour validation rapide.
"""

import sys
import time
import random
import requests
from bs4 import BeautifulSoup

# Importer les fonctions du scraper
sys.path.insert(0, '/Users/diegoclaes/Code/LP_Pharma/src')
from scraper import rotate_headers, human_like_delay, log_blocking_error, print_blocking_report

# CNK de test (exemple: Dafalgan 500mg - produit commun)
TEST_CNK = "0168536"  # Dafalgan 500mg
TEST_PRODUCT_NAME = "Dafalgan 500mg"

print("="*70)
print("🧪 TEST ANTI-DÉTECTION - Farmaline & NewPharma")
print("="*70)
print(f"\n📦 Produit test: {TEST_PRODUCT_NAME} (CNK: {TEST_CNK})")

# ============================================================================
# TEST 1: FARMALINE
# ============================================================================
print("\n" + "="*70)
print("1️⃣  TEST FARMALINE")
print("="*70)

# Catégories courantes à tester
farmaline_categories = [
    "medicaments",
    "douleur-fievre-grippe",
    "bien-etre",
    "sante"
]

farmaline_found = False
farmaline_price = None

for cat in farmaline_categories:
    url = f"https://www.farmaline.be/fr/{cat}/BE0{TEST_CNK}/"
    print(f"\n🔍 Test URL: {url}")
    
    headers = rotate_headers()
    print(f"   User-Agent: {headers['User-Agent'][:50]}...")
    print(f"   Accept-Language: {headers['Accept-Language']}")
    
    # Délai humain
    delay = human_like_delay()
    print(f"   ⏱️  Délai humain: {delay:.2f}s")
    time.sleep(delay)
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code == 403:
            log_blocking_error('farmaline', 403)
            print("   ❌ BLOQUÉ (403) - Anti-détection insuffisant")
            break
        elif resp.status_code == 429:
            log_blocking_error('farmaline', 429)
            print("   ⚠️  Rate limit (429)")
            break
        elif resp.status_code == 200:
            html = resp.text
            if "CNK" in html and f"BE0{TEST_CNK}" in html:
                soup = BeautifulSoup(html, "lxml")
                
                # Chercher le prix
                price_div = soup.find(
                    "div",
                    class_="text-xl font-bold text-dark-brand desktop:ml-3.5",
                    attrs={"data-qa-id": "product-page-variant-details__display-price"}
                )
                
                if price_div:
                    price_str = price_div.get_text(strip=True).replace("€","").replace("\xa0","").replace(",",".")
                    farmaline_price = float(price_str)
                    farmaline_found = True
                    print(f"   ✅ TROUVÉ! Prix: {farmaline_price}€")
                    break
                else:
                    print("   ⚠️  Produit trouvé mais prix non extrait")
            else:
                print("   ❓ CNK non trouvé dans cette catégorie")
        else:
            print(f"   ❓ Status inattendu: {resp.status_code}")
            
    except requests.exceptions.Timeout:
        print("   ⏱️  Timeout (15s dépassé)")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

# Résumé Farmaline
print("\n" + "-"*70)
if farmaline_found:
    print(f"✅ Farmaline: SUCCÈS - Prix trouvé: {farmaline_price}€")
else:
    print("❌ Farmaline: ÉCHEC - Produit non trouvé ou bloqué")

# ============================================================================
# TEST 2: NEWPHARMA
# ============================================================================
print("\n" + "="*70)
print("2️⃣  TEST NEWPHARMA")
print("="*70)

url = f"https://www.newpharma.be/fr/search-results/search.html?q={TEST_PRODUCT_NAME.replace(' ', '+')}"
print(f"\n🔍 Test URL: {url}")

headers = rotate_headers()
headers["Referer"] = "https://www.newpharma.be/"
print(f"   User-Agent: {headers['User-Agent'][:50]}...")
print(f"   Accept-Language: {headers['Accept-Language']}")

# Délai humain
delay = human_like_delay()
print(f"   ⏱️  Délai humain: {delay:.2f}s")
time.sleep(delay)

newpharma_found = False
newpharma_price = None

try:
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 403:
        log_blocking_error('newpharma', 403)
        print("   ❌ BLOQUÉ (403) - Cloudflare ou anti-bot actif")
    elif resp.status_code == 429:
        log_blocking_error('newpharma', 429)
        print("   ⚠️  Rate limit (429)")
    elif resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "lxml")
        divs = soup.find_all("div", attrs={"data-google-360": True})
        
        print(f"   📊 {len(divs)} div(s) avec data-google-360 trouvés")
        
        if divs:
            import json
            for div in divs:
                raw = div.get("data-google-360", "")
                try:
                    data = json.loads(raw.replace("&quot;", '"'))
                    items = data.get("ecommerce", {}).get("items", [])
                    
                    for item in items:
                        item_name = item.get("item_name", "")
                        price = item.get("price")
                        
                        # Fuzzy match simple
                        if TEST_PRODUCT_NAME.lower() in item_name.lower() or "dafalgan" in item_name.lower():
                            newpharma_price = price
                            newpharma_found = True
                            print(f"   ✅ TROUVÉ! {item_name} - Prix: {price}€")
                            break
                    
                    if newpharma_found:
                        break
                except:
                    continue
        else:
            print("   ❌ Aucun produit trouvé avec data-google-360")
    else:
        print(f"   ❓ Status inattendu: {resp.status_code}")
        
except requests.exceptions.Timeout:
    print("   ⏱️  Timeout (30s dépassé)")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Résumé NewPharma
print("\n" + "-"*70)
if newpharma_found:
    print(f"✅ NewPharma: SUCCÈS - Prix trouvé: {newpharma_price}€")
else:
    print("❌ NewPharma: ÉCHEC - Produit non trouvé ou bloqué")

# ============================================================================
# RAPPORT FINAL
# ============================================================================
print("\n" + "="*70)
print("📊 RAPPORT FINAL")
print("="*70)

print_blocking_report()

print("\n💡 Résumé:")
print(f"   • Farmaline: {'✅ Fonctionne' if farmaline_found else '❌ Bloqué ou non trouvé'}")
print(f"   • NewPharma: {'✅ Fonctionne' if newpharma_found else '❌ Bloqué ou non trouvé'}")

if farmaline_found and newpharma_found:
    print("\n🎉 Excellente nouvelle: L'anti-détection semble fonctionner!")
    print("   Vous pouvez lancer un test complet avec --limit 10 pour validation.")
elif farmaline_found or newpharma_found:
    print("\n⚠️  Résultats mitigés: Un site fonctionne, l'autre non.")
    print("   Consultez docs/ANTI_DETECTION_AVANCEE.md pour solutions avancées.")
else:
    print("\n❌ Aucun site ne fonctionne - Solutions recommandées:")
    print("   1. VPS en Belgique (5€/mois)")
    print("   2. ScraperAPI (2€/mois)")
    print("   3. Playwright + Cloudflare bypass")
    print("\n   Voir docs/ANTI_DETECTION_AVANCEE.md pour détails complets.")

print("\n" + "="*70)
