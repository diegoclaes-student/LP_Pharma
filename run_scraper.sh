#!/bin/bash

# Script de lancement du scraper LP_Pharma
# Usage: ./run_scraper.sh [input_file] [output_file]

# Chemins par défaut
DEFAULT_INPUT="data/input/grid.csv"
DEFAULT_OUTPUT="data/output/resultats_$(date +%Y%m%d_%H%M%S).csv"

# Utiliser les arguments ou les valeurs par défaut
INPUT_FILE="${1:-$DEFAULT_INPUT}"
OUTPUT_FILE="${2:-$DEFAULT_OUTPUT}"

# Vérifier que le fichier d'entrée existe
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Erreur: fichier d'entrée '$INPUT_FILE' introuvable"
    echo ""
    echo "Usage: ./run_scraper.sh [input_file] [output_file]"
    echo "Exemple: ./run_scraper.sh data/input/grid.csv data/output/resultats.csv"
    exit 1
fi

echo "============================================================"
echo "🏥 LP_PHARMA - Price Scraper"
echo "============================================================"
echo "📥 Input:  $INPUT_FILE"
echo "📤 Output: $OUTPUT_FILE"
echo "============================================================"
echo ""

# Lancer le scraper
conda run -n scraping python src/scraper.py "$INPUT_FILE" "$OUTPUT_FILE"

echo ""
echo "✅ Terminé! Résultats disponibles dans: $OUTPUT_FILE"
