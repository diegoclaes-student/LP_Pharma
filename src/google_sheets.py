#!/usr/bin/env python3
"""
Module Google Sheets pour LP_Pharma
Gère la lecture des CNK et l'écriture des résultats de scraping dans Google Sheets.

Authentification : Service Account (recommandé)
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import gspread
from google.oauth2.service_account import Credentials


# Scopes requis pour Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    # drive.readonly allows listing/opening files shared with the service account
    'https://www.googleapis.com/auth/drive.readonly'
]


def get_credentials(creds_path: Optional[str] = None) -> Credentials:
    """
    Obtenir les credentials du Service Account.
    
    Args:
        creds_path: Chemin vers le fichier JSON du service account.
                   Si None, utilise GOOGLE_APPLICATION_CREDENTIALS env var.
    
    Returns:
        Credentials object pour authentification
    
    Raises:
        FileNotFoundError: Si le fichier de credentials n'existe pas
        ValueError: Si les credentials sont invalides
    """
    if creds_path is None:
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            # Fallback vers le chemin recommandé (expand ~ to home directory)
            default_path = Path.home() / '.config' / 'lp_pharma' / 'sa_key.json'
            if default_path.exists():
                creds_path = str(default_path)
            else:
                raise FileNotFoundError(
                    "Aucun fichier de credentials trouvé. "
                    "Définissez GOOGLE_APPLICATION_CREDENTIALS ou placez le fichier dans "
                    f"{default_path}"
                )
    
    # Expand ~ to home directory if present
    creds_path = str(Path(creds_path).expanduser())
    
    if not Path(creds_path).exists():
        raise FileNotFoundError(f"Fichier de credentials introuvable: {creds_path}")
    
    print(f"🔑 Authentification avec: {creds_path}")
    credentials = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return credentials


def open_sheet(sheet_name: str, creds_path: Optional[str] = None) -> gspread.Spreadsheet:
    """
    Ouvre une Google Sheet par son nom.
    
    Args:
        sheet_name: Nom de la Google Sheet (ex: "test_pharma_scrap")
        creds_path: Chemin vers le fichier de credentials (optionnel)
    
    Returns:
        gspread.Spreadsheet object
    
    Raises:
        gspread.exceptions.SpreadsheetNotFound: Si la feuille n'existe pas ou n'est pas partagée
    """
    credentials = get_credentials(creds_path)
    client = gspread.authorize(credentials)
    
    print(f"📊 Ouverture de la Google Sheet: {sheet_name}")
    try:
        spreadsheet = client.open(sheet_name)
        print(f"✅ Sheet ouverte: {spreadsheet.url}")
        return spreadsheet
    except gspread.exceptions.SpreadsheetNotFound:
        raise gspread.exceptions.SpreadsheetNotFound(
            f"Google Sheet '{sheet_name}' introuvable. "
            "Vérifiez que:\n"
            "  1. Le nom est correct\n"
            "  2. La feuille est partagée avec le service account email\n"
            "  3. Le service account a les permissions 'Éditeur'"
        )


def read_cnks(
    spreadsheet: gspread.Spreadsheet,
    worksheet_name: str = 'resultats_final',
    cnk_col: str = 'CNK',
    name_col: str = 'Nom_Produit'
) -> Tuple[List[str], Dict[str, int], Dict[str, str]]:
    """
    Lit la liste des CNK depuis une worksheet.
    
    Args:
        spreadsheet: gspread.Spreadsheet object
        worksheet_name: Nom de l'onglet (ex: "resultats_final")
        cnk_col: Nom de la colonne contenant les CNK (ex: "CNK")
    
    Returns:
        Tuple de (liste des CNK, mapping CNK -> numéro de ligne)
        Le mapping permet de retrouver la ligne pour écrire les résultats
    
    Raises:
        ValueError: Si la colonne CNK n'existe pas ou est vide
    """
    print(f"\n📖 Lecture des CNK depuis l'onglet '{worksheet_name}'...")
    
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        raise ValueError(
            f"Onglet '{worksheet_name}' introuvable dans la Google Sheet. "
            f"Onglets disponibles: {[ws.title for ws in spreadsheet.worksheets()]}"
        )
    
    # Récupérer toutes les valeurs (plus rapide qu'une lecture cellule par cellule)
    all_values = worksheet.get_all_values()
    
    if not all_values:
        raise ValueError(f"L'onglet '{worksheet_name}' est vide")
    
    # Trouver l'index de la colonne CNK dans la première ligne (headers)
    headers = all_values[0]
    try:
        cnk_col_idx = headers.index(cnk_col)
    except ValueError:
        raise ValueError(
            f"Colonne '{cnk_col}' introuvable dans l'onglet '{worksheet_name}'. "
            f"Colonnes disponibles: {headers}"
        )
    
    # Trouver l'index optionnel de la colonne Nom_Produit
    try:
        name_col_idx = headers.index(name_col)
    except ValueError:
        name_col_idx = None

    # Extraire les CNK (ignorer la ligne d'en-tête et les cellules vides)
    cnk_list = []
    cnk_to_row = {}  # Mapping CNK -> numéro de ligne (1-based, pour Google Sheets)
    cnk_to_name = {}

    for row_idx, row in enumerate(all_values[1:], start=2):  # start=2 car ligne 1 = headers
        if len(row) > cnk_col_idx:
            cnk = row[cnk_col_idx].strip()
            if cnk:  # Ignorer les cellules vides
                cnk_list.append(cnk)
                cnk_to_row[cnk] = row_idx
                # Lire le nom du produit si la colonne existe
                if name_col_idx is not None and len(row) > name_col_idx:
                    cnk_to_name[cnk] = row[name_col_idx].strip()
                else:
                    cnk_to_name[cnk] = ''
    
    print(f"✅ {len(cnk_list)} CNKs trouvés dans la colonne '{cnk_col}'")
    
    if not cnk_list:
        raise ValueError(f"Aucun CNK trouvé dans la colonne '{cnk_col}'")

    return cnk_list, cnk_to_row, cnk_to_name


def write_results(
    spreadsheet: gspread.Spreadsheet,
    worksheet_name: str,
    cnk_to_row: Dict[str, int],
    results: Dict[str, Dict[str, any]],
    retry_count: int = 2,
    retry_delay: float = 2.0
) -> None:
    """
    Écrit les résultats du scraping dans la Google Sheet (batch mode).
    
    Args:
        spreadsheet: gspread.Spreadsheet object
        worksheet_name: Nom de l'onglet
        cnk_to_row: Mapping CNK -> numéro de ligne
        results: Dict avec les résultats pour chaque CNK
                 Format: {'CNK': {'Prix_MediMarket': 12.34, 'Prix_Multipharma': 10.5, ...}}
        retry_count: Nombre de tentatives en cas d'erreur API
        retry_delay: Délai entre les tentatives (secondes)
    
    Les colonnes écrites :
        - Prix_MediMarket
        - Prix_Farmaline
        - Prix_NewPharma
        - Prix_Multipharma
        - Match_Multipharma
        - Match_NewPharma
        - Match_Source_Multipharma
        - Prix Moyen
        - Prix Min
    """
    print(f"\n📝 Écriture des résultats dans l'onglet '{worksheet_name}'...")
    
    worksheet = spreadsheet.worksheet(worksheet_name)
    
    # Récupérer les headers pour trouver les index de colonnes
    headers = worksheet.row_values(1)
    
    # Mapping des colonnes à écrire (nom -> index)
    columns_to_write = {
        'Prix_MediMarket': None,
        'Prix_Farmaline': None,
        'Prix_NewPharma': None,
        'Prix_Multipharma': None,
        'Match_Multipharma': None,
        'Match_NewPharma': None,
        'Match_Source_Multipharma': None,
        'Prix Moyen': None,
        'Prix Min': None,
    }
    
    # Trouver les index des colonnes
    for col_name in columns_to_write.keys():
        try:
            columns_to_write[col_name] = headers.index(col_name)
        except ValueError:
            print(f"⚠️  Colonne '{col_name}' introuvable dans les headers. Ignorée.")
    
    # Filtrer les colonnes qui existent réellement
    columns_to_write = {k: v for k, v in columns_to_write.items() if v is not None}
    
    if not columns_to_write:
        raise ValueError(
            "Aucune colonne de résultat trouvée dans la feuille. "
            f"Headers disponibles: {headers}"
        )
    
    print(f"📊 Colonnes à mettre à jour: {list(columns_to_write.keys())}")
    
    # Préparer les updates (batch)
    # Format: liste de dicts avec 'range' et 'values'
    updates = []
    
    for cnk, data in results.items():
        if cnk not in cnk_to_row:
            print(f"⚠️  CNK {cnk} non trouvé dans le mapping des lignes. Ignoré.")
            continue
        
        row_num = cnk_to_row[cnk]
        
        for col_name, col_idx in columns_to_write.items():
            # Convertir l'index de colonne en lettre (A, B, C, ...)
            col_letter = chr(65 + col_idx)  # 65 = 'A'
            cell_range = f"{col_letter}{row_num}"
            
            # Récupérer la valeur à écrire
            value = data.get(col_name, '')
            
            # Formater la valeur
            if value == '' or value is None:
                formatted_value = ''
            elif isinstance(value, (int, float)):
                # Keep numeric types as-is so Google Sheets stores them as numbers.
                # Formatting (comma decimal / two decimals) will be applied to the column below.
                formatted_value = value
            else:
                # Ensure booleans/others are stringified
                formatted_value = str(value)
            
            updates.append({
                'range': cell_range,
                'values': [[formatted_value]]
            })
    
    if not updates:
        print("⚠️  Aucune donnée à écrire")
        return
    
    print(f"📤 Envoi de {len(updates)} mises à jour...")
    
    # Écrire en batch avec retry
    for attempt in range(retry_count + 1):
        try:
            worksheet.batch_update(updates)
            print(f"✅ {len(updates)} cellules mises à jour avec succès")
            # Après écriture, appliquer un format numérique (2 décimales) aux colonnes pertinentes
            try:
                # Colonnes numériques à formater avec 2 décimales (virgule)
                numeric_cols = ['Prix_MediMarket', 'Prix_Farmaline', 'Prix_NewPharma', 'Prix_Multipharma', 'Prix Moyen', 'Prix Min']
                for col_name in numeric_cols:
                    if col_name in columns_to_write:
                        col_idx = columns_to_write[col_name]
                        # Convert index to letter (A=0)
                        col_letter = chr(65 + col_idx)
                        # Format range from row 2 to end of column
                        range_a1 = f"{col_letter}2:{col_letter}"
                        fmt = {
                            "numberFormat": {
                                "type": "NUMBER",
                                "pattern": "#,##0.00"
                            }
                        }
                        try:
                            worksheet.format(range_a1, {"numberFormat": fmt["numberFormat"]})
                        except Exception as e:
                            # Non-fatal: log and continue
                            print(f"⚠️  Impossible d'appliquer le format numérique à {col_name}: {e}")
                
                # Match scores: format décimal à 3 chiffres (0,995)
                for match_col in ['Match_Multipharma', 'Match_NewPharma']:
                    if match_col in columns_to_write:
                        col_idx = columns_to_write[match_col]
                        col_letter = chr(65 + col_idx)
                        range_a1 = f"{col_letter}2:{col_letter}"
                        fmt_match = {
                            "numberFormat": {
                                "type": "NUMBER",
                                "pattern": "0,00#"  # Format décimal: 0,00 jusqu'à 3 décimales (sans zéros inutiles)
                            }
                        }
                        try:
                            worksheet.format(range_a1, {"numberFormat": fmt_match["numberFormat"]})
                        except Exception as e:
                            print(f"⚠️  Impossible d'appliquer le format à {match_col}: {e}")
            except Exception as e:
                print(f"⚠️  Erreur lors de l'application des formats de colonnes: {e}")
            return
        except Exception as e:
            if attempt < retry_count:
                print(f"⚠️  Erreur lors de l'écriture (tentative {attempt + 1}/{retry_count + 1}): {e}")
                print(f"⏳ Attente de {retry_delay}s avant nouvelle tentative...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Backoff exponentiel
            else:
                print(f"❌ Échec de l'écriture après {retry_count + 1} tentatives")
                raise


def calculate_stats(results: Dict[str, Dict[str, any]]) -> Dict[str, Dict[str, any]]:
    """
    Calcule les statistiques (Prix Moyen, Prix Min) pour chaque CNK.
    
    Args:
        results: Dict avec les résultats pour chaque CNK
    
    Returns:
        Le même dict enrichi avec 'Prix Moyen' et 'Prix Min'
    """
    print("\n📊 Calcul des statistiques (Prix Moyen, Prix Min)...")
    
    for cnk, data in results.items():
        prices = []
        
        # Collecter les prix disponibles (tous les sites)
        for price_col in ['Prix_MediMarket', 'Prix_Farmaline', 'Prix_NewPharma', 'Prix_Multipharma']:
            if price_col in data and data[price_col] not in ('', 'NA', None):
                try:
                    price = float(data[price_col])
                    prices.append(price)
                except (ValueError, TypeError):
                    pass
        
        # Calculer moyenne et min
        if prices:
            data['Prix Moyen'] = round(sum(prices) / len(prices), 2)
            data['Prix Min'] = round(min(prices), 2)
        else:
            data['Prix Moyen'] = ''
            data['Prix Min'] = ''
    
    print(f"✅ Statistiques calculées pour {len(results)} CNKs")
    return results


if __name__ == "__main__":
    # Test simple du module
    print("🧪 Test du module google_sheets.py")
    print("\nPour tester:")
    print("  1. Configurez votre Service Account")
    print("  2. Partagez votre Google Sheet avec le SA email")
    print("  3. Exécutez: python src/google_sheets.py")
