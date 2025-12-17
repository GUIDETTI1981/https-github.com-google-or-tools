#!/bin/bash

################################################################################
# Valhalla Data Initialization Script
# 
# Questo script scarica, configura e costruisce i tile di routing Valhalla
# per supportare routing camion con vincoli fisici (peso, altezza, larghezza)
#
# Autore: Senior DevOps Engineer
# Data: 2025-12-17
################################################################################

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurazione
REGION="${1:-italy}"  # Default: italy
DATA_DIR="./valhalla-data"
GEOFABRIK_BASE="https://download.geofabrik.de/europe"

# Mappa delle regioni disponibili
declare -A REGIONS=(
    ["italy"]="italy-latest.osm.pbf"
    ["central-italy"]="central-italy-latest.osm.pbf"
    ["lazio"]="lazio-latest.osm.pbf"
    ["lombardia"]="lombardia-latest.osm.pbf"
    ["rome"]="central-italy-latest.osm.pbf"
)

# Funzione per stampare con colori
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Banner
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Valhalla Data Initialization Script               ║${NC}"
echo -e "${BLUE}║     Truck Routing with Physical Constraints            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verifica Docker
print_info "Verifica installazione Docker..."
if ! command -v docker &> /dev/null; then
    print_error "Docker non trovato! Installa Docker prima di continuare."
    exit 1
fi
print_success "Docker installato"

# Determina il file da scaricare
if [[ -n "${REGIONS[$REGION]}" ]]; then
    MAP_FILE="${REGIONS[$REGION]}"
else
    print_warning "Regione '$REGION' non trovata, uso 'italy' come default"
    REGION="italy"
    MAP_FILE="${REGIONS[$REGION]}"
fi

print_info "Regione selezionata: $REGION"
print_info "File mappa: $MAP_FILE"

# URL download
if [[ "$REGION" == "italy" ]]; then
    DOWNLOAD_URL="$GEOFABRIK_BASE/$MAP_FILE"
elif [[ "$REGION" == "central-italy" || "$REGION" == "rome" ]]; then
    DOWNLOAD_URL="$GEOFABRIK_BASE/italy/$MAP_FILE"
elif [[ "$REGION" == "lazio" || "$REGION" == "lombardia" ]]; then
    DOWNLOAD_URL="$GEOFABRIK_BASE/italy/$MAP_FILE"
else
    DOWNLOAD_URL="$GEOFABRIK_BASE/$MAP_FILE"
fi

# Crea directory
print_info "Creazione directory $DATA_DIR..."
mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

# Estrai nome base
MAP_BASENAME="${MAP_FILE%.osm.pbf}"

# Step 1: Download mappa (se non esiste)
if [[ -f "$MAP_FILE" ]]; then
    print_warning "File $MAP_FILE già esistente, skip download"
else
    print_info "Download mappa da Geofabrik..."
    print_info "URL: $DOWNLOAD_URL"
    print_info "Dimensione stimata: 200MB-1GB (dipende dalla regione)"
    
    if command -v wget &> /dev/null; then
        wget -c "$DOWNLOAD_URL" -O "$MAP_FILE"
    elif command -v curl &> /dev/null; then
        curl -L "$DOWNLOAD_URL" -o "$MAP_FILE"
    else
        print_error "Né wget né curl sono disponibili. Installa uno dei due."
        exit 1
    fi
    
    print_success "Download completato: $MAP_FILE"
fi

FILE_SIZE=$(du -h "$MAP_FILE" | cut -f1)
print_info "Dimensione file: $FILE_SIZE"

# Step 2: Genera configurazione Valhalla
print_info "Step 2/4: Generazione configurazione Valhalla..."

if [[ -f "valhalla.json" ]]; then
    print_warning "valhalla.json già esistente, skip generazione"
else
    print_info "Creazione valhalla.json con configurazione ottimizzata per camion..."
    
    # Genera config usando il container Valhalla
    docker run --rm -v "$PWD:/data" gisops/valhalla:latest \
        valhalla_build_config \
        --mjolnir-tile-dir /data/valhalla_tiles \
        --mjolnir-tile-extract /data/valhalla_tiles.tar \
        --mjolnir-timezone /data/valhalla_tiles/timezones.sqlite \
        --mjolnir-admin /data/valhalla_tiles/admins.sqlite > valhalla.json
    
    # Modifica porta nel config (da 8002)
    if command -v sed &> /dev/null; then
        sed -i 's/"port": [0-9]*/"port": 8002/' valhalla.json 2>/dev/null || \
        sed -i '' 's/"port": [0-9]*/"port": 8002/' valhalla.json 2>/dev/null
    fi
    
    print_success "Configurazione generata: valhalla.json"
fi

# Step 3: Build Admin Database (confini amministrativi)
print_info "Step 3/4: Costruzione database amministrativo..."
print_info "Tempo stimato: 1-3 minuti"

if [[ -f "valhalla_tiles/admins.sqlite" ]]; then
    print_warning "Admin DB già esistente, skip build"
else
    docker run --rm -v "$PWD:/data" gisops/valhalla:latest \
        valhalla_build_admins \
        --config /data/valhalla.json \
        /data/"$MAP_FILE"
    
    print_success "Admin database costruito"
fi

# Step 4: Build Routing Tiles (il cuore del routing)
print_info "Step 4/4: Costruzione tile di routing..."
print_info "Tempo stimato: 5-20 minuti (dipende dalla dimensione mappa)"
print_info "Questo è il passo più lungo, sii paziente..."

if [[ -d "valhalla_tiles" ]] && [[ $(ls -A valhalla_tiles/*.gph 2>/dev/null | wc -l) -gt 0 ]]; then
    print_warning "Tile già esistenti, skip build"
    print_info "Per forzare rebuild: rm -rf valhalla_tiles"
else
    # Build tiles con supporto completo truck
    docker run --rm -v "$PWD:/data" gisops/valhalla:latest \
        valhalla_build_tiles \
        --config /data/valhalla.json \
        /data/"$MAP_FILE"
    
    print_success "Tile di routing costruiti"
fi

# Verifica files generati
echo ""
print_info "Files generati in $DATA_DIR:"
ls -lh valhalla.json 2>/dev/null || true
ls -lh "$MAP_FILE" 2>/dev/null || true
print_info "Tile directory:"
ls -lh valhalla_tiles/*.sqlite 2>/dev/null | head -5 || true
print_info "Graph tiles:"
find valhalla_tiles -name "*.gph" 2>/dev/null | head -5 || true
TILE_COUNT=$(find valhalla_tiles -name "*.gph" 2>/dev/null | wc -l)
print_info "Totale tile generati: $TILE_COUNT"

# Calcola spazio disco
TOTAL_SIZE=$(du -sh . | cut -f1)
print_info "Spazio totale occupato: $TOTAL_SIZE"

# Success message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            ✅ VALHALLA SETUP COMPLETATO! ✅              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
print_success "Valhalla è pronto per il routing camion!"
echo ""
print_info "File chiave generati:"
echo -e "  ${YELLOW}valhalla.json${NC}         - Configurazione server"
echo -e "  ${YELLOW}valhalla_tiles/admins.sqlite${NC}  - Database confini"
echo -e "  ${YELLOW}valhalla_tiles/*.gph${NC}  - Tile di routing ($TILE_COUNT files)"
echo ""
print_info "Per avviare Valhalla, esegui:"
echo -e "  ${YELLOW}docker-compose up valhalla${NC}"
echo ""
print_info "Per testare Valhalla, esegui:"
echo -e "  ${YELLOW}curl 'http://localhost:8002/status'${NC}"
echo ""
print_info "Per avviare l'intera applicazione:"
echo -e "  ${YELLOW}docker-compose up${NC}"
echo ""

# Cleanup opzionale
read -p "Vuoi cancellare il file .osm.pbf originale per risparmiare spazio? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    rm -f "$MAP_FILE"
    print_success "File $MAP_FILE rimosso"
    SAVED_SIZE=$FILE_SIZE
    print_info "Spazio risparmiato: $SAVED_SIZE"
else
    print_info "File $MAP_FILE mantenuto"
fi

echo ""
print_success "Script completato con successo! 🎉"
print_info "Valhalla supporta ora:"
echo "  • 🚛 Routing camion con vincoli peso"
echo "  • 📏 Restrizioni altezza e larghezza"
echo "  • ☣️  Gestione merci pericolose (hazmat)"
echo "  • 🚫 Restrizioni stradali automatiche"
echo "  • ⏱️  Calcolo tempi accurato per heavy vehicles"
