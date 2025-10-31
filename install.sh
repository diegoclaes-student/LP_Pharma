#!/bin/bash
# Script d'installation des dépendances pour LP_Pharma

set -e  # Exit on error

echo "🔧 Installation des dépendances LP_Pharma"
echo "=========================================="
echo ""

# Vérifier que conda est disponible
if ! command -v conda &> /dev/null; then
    echo "❌ Erreur: conda n'est pas installé ou n'est pas dans le PATH"
    echo "   Installez Miniconda ou Anaconda d'abord"
    exit 1
fi

# Vérifier si l'environnement existe déjà
if conda env list | grep -q "^scraping "; then
    echo "✅ L'environnement 'scraping' existe déjà"
    echo "   Pour réinstaller: conda env remove -n scraping && ./install.sh"
else
    echo "📦 Création de l'environnement conda 'scraping'..."
    conda create -n scraping python=3.11 -y
fi

echo ""
echo "📥 Installation des packages Python..."
conda run -n scraping pip install -r requirements.txt

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Pour activer l'environnement:"
echo "  conda activate scraping"
echo ""
echo "Pour tester l'installation:"
echo "  python src/scraper.py --help"
echo ""
echo "📖 Pour configurer Google Sheets, consultez: docs/GS_SETUP.md"
