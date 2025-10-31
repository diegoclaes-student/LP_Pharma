#!/usr/bin/env python3
"""
Test rapide pour vérifier si cloudscraper contourne Cloudflare sur NewPharma.
"""

import cloudscraper
import time
from bs4 import BeautifulSoup
import json

print("="*70)
print("🧪 TEST CLOUDSCRAPER - NewPharma Cloudflare Bypass")
print("="*70)

# Créer le scraper cloudscraper
print("\n1️⃣  Création du scraper cloudscraper...")
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)
print("   ✅ Scraper créé")

# Test 1: Page d'accueil
print("\n2️⃣  Test page d'accueil NewPharma...")
try:
    resp = scraper.get('https://www.newpharma.be/pharmacie/', timeout=30)
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200:
        print("   ✅ Accès réussi!")
        # Vérifier si on a le vrai contenu ou une page Cloudflare
        if 'Attention Required' in resp.text or 'Cloudflare' in resp.text[:1000]:
            print("   ❌ Page Cloudflare Challenge détectée")
        else:
            print("   ✅ Contenu réel obtenu (pas de Cloudflare)")
    elif resp.status_code == 403:
        print("   ❌ BLOQUÉ (403) - cloudscraper n'a pas suffi")
    else:
        print(f"   ⚠️  Status inattendu: {resp.status_code}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Test 2: Recherche produit
print("\n3️⃣  Test recherche produit (Dafalgan)...")
time.sleep(2)  # Petit délai entre les requêtes

try:
    url = 'https://www.newpharma.be/fr/search-results/search.html?q=dafalgan'
    resp = scraper.get(url, timeout=30)
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200:
        print("   ✅ Recherche réussie!")
        
        # Parser et chercher les produits
        soup = BeautifulSoup(resp.content, "lxml")
        divs = soup.find_all("div", attrs={"data-google-360": True})
        
        print(f"   📊 {len(divs)} div(s) avec data-google-360 trouvés")
        
        if divs:
            print("\n   🎯 Produits trouvés:")
            for i, div in enumerate(divs[:3]):  # Afficher les 3 premiers
                raw = div.get("data-google-360", "")
                try:
                    data = json.loads(raw.replace("&quot;", '"'))
                    items = data.get("ecommerce", {}).get("items", [])
                    
                    for item in items:
                        name = item.get("item_name", "")
                        price = item.get("price", "")
                        if name and price:
                            print(f"      • {name[:60]}... → {price}€")
                            break
                except:
                    pass
            
            print("\n   ✅ cloudscraper FONCTIONNE! NewPharma accessible!")
        else:
            print("   ⚠️  Aucun produit trouvé (structure HTML différente?)")
            
    elif resp.status_code == 403:
        print("   ❌ BLOQUÉ (403) - cloudscraper insuffisant")
        print("   → Solution: VPS Belgique ou Playwright requis")
    else:
        print(f"   ⚠️  Status inattendu: {resp.status_code}")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print("\n" + "="*70)
print("📊 CONCLUSION")
print("="*70)
print("Si vous voyez '✅ cloudscraper FONCTIONNE', vous pouvez:")
print("  1. Lancer un test complet avec --limit 10")
print("  2. Scraper NewPharma sans problème!")
print("\nSi vous voyez '❌ BLOQUÉ', il faudra:")
print("  1. Essayer un VPS en Belgique (5€/mois)")
print("  2. Ou utiliser Playwright + cloudscraper")
print("="*70)
