# Intégration Google Sheets — Plan d'implémentation

Objectif : lire une colonne `CNK` depuis une Google Sheet (onglet `resultats_final`) et écrire les prix scrappés dans les colonnes de cette même feuille.

---

## Contexte et décisions utilisateurs

- Nom de la Google Sheet cible : `test_pharma_scrap`
- Onglet/tab : la feuille contenant les résultats s'appelle `resultats_final`
- Les CNK se trouvent dans la colonne **B** (colonne index 2)
- Comportement d'écriture : **écrase toujours** les colonnes de prix (écriture complète)
- Authentification : **Service Account** (recommandé pour automatisation)
- Taille typique : entre **100 et 1000** lignes
- Écriture : **batch** à la fin du run (écrire une seule fois, pas ligne par ligne)
- Colonnes supplémentaires à écrire : `Prix Moyen`, `Prix Min`

---

## Mapping des colonnes (proposé)

Feuille `resultats_final` colonnes attendues (exemple) :

- Col A : `Nom_Produit` (optionnel)
- Col B : `CNK`  <-- lecture
- Col C : `Prix_Base`
- Col D : `Prix_MediMarket`  <-- écriture
- Col E : `Prix_Multipharma` <-- écriture
- Col F : `Prix_NewPharma`    <-- écriture (désactivé)
- Col G : `Match_Multipharma`
- Col H : `Match_NewPharma`
- Col I : `Prix Moyen`        <-- écriture demandée
- Col J : `Prix Min`          <-- écriture demandée

> Remarque : si les colonnes diffèrent, on cherchera les en-têtes par nom (recommandé) plutôt que par index fixe.

---

## Authentification — Service Account (procédure résumée)

1. Aller dans Google Cloud Console → APIs & Services → Credentials
2. Créer un **Service Account** (ex: `lp-pharma-scraper-sa`) et générer une clé JSON
3. Activer l'API Google Sheets pour le projet
4. Partager la feuille Google Sheet `test_pharma_scrap` avec l'adresse e-mail du Service Account (ex: `lp-pharma-scraper-sa@PROJECT.iam.gserviceaccount.com`) en mode éditeur
5. Placer le fichier JSON de clé sur la machine qui exécute le scraper (ex: `~/.config/lp_pharma/sa_key.json`) et **ne pas** le committer dans Git
6. Ajouter une variable d'environnement `GOOGLE_APPLICATION_CREDENTIALS=~/.config/lp_pharma/sa_key.json` ou fournir le chemin au module `google_sheets.py`

---

## Implémentation technique proposée

1. Dépendances

- `gspread`
- `google-auth` (ou `google-auth-httplib2`)

Installation :

```bash
pip install gspread google-auth
```

2. Nouveau module : `src/google_sheets.py`

Fonctions prévues :

- `open_sheet(sheet_id_or_name, creds_path=None) -> gspread.Spreadsheet`
- `read_cnks(spreadsheet, worksheet_name='resultats_final', cnk_col='CNK') -> List[str]`
- `write_results(spreadsheet, worksheet_name, start_row, rows, headers_map)`
  - `rows` sera une liste de dicts `{ 'CNK': '123', 'Prix_Multipharma': '12.34', ... }`
  - `headers_map` mappe les clés aux noms de colonnes dans la feuille

3. Performance & quotas

- Taille prévue 100-1000 lignes → faire la lecture complète en 1 appel, préparer un tableau 2D et écrire en une seule opération `worksheet.update(range, values)` pour minimiser les appels API
- Batch-size : écrire tout en fin de run

4. Robustesse

- Vérifier que la feuille contient bien la colonne `CNK` en tête; si non, échouer proprement avec message d'erreur
- Journaliser le nombre de lignes lues et écrites
- En cas d'erreur API, réessayer 2 fois avec backoff exponentiel

---

## Intégration avec `src/scraper.py`

- Ajouter un argument `--sheet` ou `--sheet-id <ID>` pour activer le mode Google Sheet
- Si `--sheet` activé, le script lira la colonne `CNK` dans la feuille `test_pharma_scrap` et exécutera le scrape pour ces CNK
- À la fin du run, préparer les colonnes demandées (`Prix_Multipharma`, `Prix_MediMarket`, `Prix Moyen`, `Prix Min`, `Match_*`, `Source_*`) et écrire toutes les lignes en batch dans la feuille

---

## Tests

- Créer une google sheet d'essai `test_pharma_scrap` (ex: onglet `resultats_final`) avec 10-20 lignes pour test e2e
- Tests unitaires : mocker `gspread` pour vérifier mapping de colonnes et format d'écriture
- Test de charge : exécuter sur 500 lignes en local pour vérifier le temps et les quotas

---

## Sécurité & gestion des secrets

- Ne pas commit le JSON du Service Account
- `.gitignore` doit exclure le chemin de stockage recommandé
- Documenter clairement où placer la clé et comment définir `GOOGLE_APPLICATION_CREDENTIALS`

---

## Livrables (après implémentation)

- `src/google_sheets.py` (module d'IO Google Sheets)
- `src/scraper.py` supportant `--sheet` (lecture + écriture batch)
- `docs/GS_INTEGRATION_PLAN.md` (ce document)
- `docs/GS_SETUP.md` (procédure pas-à-pas pour créer SA et partager la feuille)
- Tests unitaires et script de démonstration

---

Si tu es d'accord avec ce plan, je passe à l'implémentation du module `src/google_sheets.py` et à l'intégration progressive dans `src/scraper.py`. Si tu veux modifier le mapping (par ex. noms de colonnes différents, autre onglet), dis-le et j'adapte avant de coder.
