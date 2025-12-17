#!/bin/bash

################################################################################
# OSRM Data Initialization Script
# 
# Questo script scarica, estrae e preprocessa le mappe OpenStreetMap
# per OSRM usando l'algoritmo MLD (Multi-Level Dijkstra)
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
REGION="${1:-italy}"  # Default: italy, puoi cambiare con: ./init_osrm.sh central-italy
DATA_DIR="./osrm-data"
GEOFABRIK_BASE="https://download.geofabrik.de/europe"

# Mappa delle regioni disponibili
declare -A REGIONS=(
    ["italy"]="italy-latest.osm.pbf"
    ["central-italy"]="central-italy-latest.osm.pbf"
    ["lazio"]="lazio-latest.osm.pbf"
    ["lombardia"]="lombardia-latest.osm.pbf"
    ["rome"]="central-italy-latest.osm.pbf"  # Alias per Roma
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
echo -e "${BLUE}║     OSRM Data Initialization Script                   ║${NC}"
echo -e "${BLUE}║     OpenStreetMap + OSRM Backend Setup                ║${NC}"
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

# URL download basato sulla struttura Geofabrik
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

# Step 1: Download mappa
if [[ -f "$MAP_FILE" ]]; then
    print_warning "File $MAP_FILE già esistente, skip download"
    print_info "Per forzare il download, cancella il file: rm $DATA_DIR/$MAP_FILE"
else
    print_info "Download mappa da Geofabrik..."
    print_info "URL: $DOWNLOAD_URL"
    print_info "Dimensione stimata: 200MB-1GB (dipende dalla regione)"
    print_info "Tempo stimato: 1-5 minuti (dipende dalla connessione)"
    
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

# Verifica dimensione file
FILE_SIZE=$(du -h "$MAP_FILE" | cut -f1)
print_info "Dimensione file: $FILE_SIZE"

# Step 2: Extract (estrai il grafo stradale)
print_info "Step 2/4: Estrazione dati stradali (OSRM Extract)..."
print_info "Tempo stimato: 2-10 minuti"

docker run -t -v "$PWD:/data" osrm/osrm-backend:latest \
    osrm-extract -p /opt/car.lua /data/"$MAP_FILE"

print_success "Estrazione completata"

# Step 3: Partition (MLD preprocessing)
print_info "Step 3/4: Partizionamento grafo (OSRM Partition - MLD)..."
print_info "Tempo stimato: 1-5 minuti"

docker run -t -v "$PWD:/data" osrm/osrm-backend:latest \
    osrm-partition /data/"$MAP_BASENAME.osrm"

print_success "Partizionamento completato"

# Step 4: Customize (ottimizzazione per query veloci)
print_info "Step 4/4: Customizzazione metriche (OSRM Customize)..."
print_info "Tempo stimato: 1-5 minuti"

docker run -t -v "$PWD:/data" osrm/osrm-backend:latest \
    osrm-customize /data/"$MAP_BASENAME.osrm"

print_success "Customizzazione completata"

# Verifica files generati
echo ""
print_info "Files generati in $DATA_DIR:"
ls -lh *.osrm* 2>/dev/null || true

# Calcola spazio disco
TOTAL_SIZE=$(du -sh . | cut -f1)
print_info "Spazio totale occupato: $TOTAL_SIZE"

# Success message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 ✅ SETUP COMPLETATO! ✅                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
print_success "OSRM è pronto per l'uso!"
echo ""
print_info "Per avviare OSRM server, esegui:"
echo -e "  ${YELLOW}docker-compose up osrm${NC}"
echo ""
print_info "Per testare OSRM, esegui:"
echo -e "  ${YELLOW}curl 'http://localhost:5000/route/v1/driving/12.4964,41.9028;12.5,41.91?overview=false'${NC}"
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
    print_info "Spazio risparmiato: $FILE_SIZE"
else
    print_info "File $MAP_FILE mantenuto"
fi

echo ""
print_success "Script completato con successo! 🎉"
