#!/bin/bash

################################################################################
# Photon Geocoder Initialization Script
# 
# Questo script scarica i dati OSM e costruisce l'indice Elasticsearch di Photon
# per il geocoding (conversione indirizzo → coordinate)
#
# Autore: Senior Data Engineer & GIS Python Developer
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
REGION="${1:-italy}"
DATA_DIR="./photon-data"
GEOFABRIK_BASE="https://download.geofabrik.de/europe"

# Mappa delle regioni disponibili
declare -A REGIONS=(
    ["italy"]="italy-latest.osm.pbf"
    ["central-italy"]="central-italy-latest.osm.pbf"
    ["lazio"]="lazio-latest.osm.pbf"
    ["lombardia"]="lombardia-latest.osm.pbf"
    ["rome"]="central-italy-latest.osm.pbf"
)

# Funzioni per stampare con colori
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
echo -e "${BLUE}║     Photon Geocoder Initialization Script             ║${NC}"
echo -e "${BLUE}║     OSM-based Address to Coordinates Conversion        ║${NC}"
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

# Step 2: Build Photon Index (Elasticsearch)
print_info "Step 2/2: Costruzione indice Photon (Elasticsearch)..."
print_info "Tempo stimato: 10-60 minuti (dipende dalla dimensione mappa)"
print_info "Questo passo costruisce l'indice per il geocoding veloce"
print_info "Richiede: ~4GB RAM, ~5GB spazio disco"

# Verifica se l'indice esiste già
if [[ -d "elasticsearch" ]]; then
    print_warning "Indice Photon già esistente in elasticsearch/"
    read -p "Vuoi ricostruirlo da zero? (s/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Skip rebuild, indice esistente verrà utilizzato"
        print_success "Setup completato! Photon è pronto."
        exit 0
    fi
    print_warning "Cancellazione indice esistente..."
    rm -rf elasticsearch
fi

# Build index con Docker
print_info "Avvio container Photon per la costruzione dell'indice..."
print_info "Questo può richiedere 10-60 minuti. Sii paziente..."

# Vai alla directory parent per montare i volumi correttamente
cd ..

# Costruisci l'indice usando il container Photon
docker run --rm \
    -v "$PWD/$DATA_DIR:/photon/photon_data" \
    -e JAVA_OPTS="-Xmx4g -Xms2g" \
    komoot/photon:latest \
    java -jar photon-*.jar \
    -nominatim-import "/photon/photon_data/$MAP_FILE" \
    -languages it,en \
    -default-language it \
    -country-codes it

# Verifica che l'indice sia stato creato
if [[ -d "$DATA_DIR/elasticsearch" ]]; then
    print_success "Indice Photon costruito con successo!"
else
    print_error "Errore: indice Photon non trovato in $DATA_DIR/elasticsearch"
    exit 1
fi

# Calcola spazio occupato
TOTAL_SIZE=$(du -sh "$DATA_DIR" | cut -f1)
print_info "Spazio totale occupato: $TOTAL_SIZE"

# Verifica file generati
echo ""
print_info "Files generati in $DATA_DIR:"
ls -lh "$DATA_DIR/$MAP_FILE" 2>/dev/null || true
print_info "Indice Elasticsearch:"
du -sh "$DATA_DIR/elasticsearch" 2>/dev/null || print_warning "Directory elasticsearch non trovata"

# Success message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            ✅ PHOTON SETUP COMPLETATO! ✅                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
print_success "Photon Geocoder è pronto per convertire indirizzi in coordinate!"
echo ""
print_info "File chiave generati:"
echo -e "  ${YELLOW}$MAP_FILE${NC}         - Mappa OSM originale"
echo -e "  ${YELLOW}elasticsearch/${NC}    - Indice Photon per geocoding"
echo ""
print_info "Per avviare Photon, esegui:"
echo -e "  ${YELLOW}docker-compose up photon${NC}"
echo ""
print_info "Per testare Photon, esegui:"
echo -e "  ${YELLOW}curl 'http://localhost:2322/api?q=Via Roma 1, Roma'${NC}"
echo ""
print_info "Per avviare l'intera applicazione:"
echo -e "  ${YELLOW}docker-compose up${NC}"
echo ""

# Cleanup opzionale
read -p "Vuoi cancellare il file .osm.pbf originale per risparmiare spazio? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    rm -f "$DATA_DIR/$MAP_FILE"
    print_success "File $MAP_FILE rimosso"
    SAVED_SIZE=$FILE_SIZE
    print_info "Spazio risparmiato: $SAVED_SIZE"
else
    print_info "File $MAP_FILE mantenuto"
fi

echo ""
print_success "Script completato con successo! 🎉"
print_info "Photon supporta ora:"
echo "  • 🗺️  Geocoding di indirizzi italiani"
echo "  • 📍 Conversione indirizzo → coordinate (lat/lon)"
echo "  • 🔍 Ricerca fuzzy (tollerante agli errori)"
echo "  • 🇮🇹 Supporto lingua italiana"
echo "  • ⚡ Ricerca veloce (indice Elasticsearch)"
echo ""
print_info "API Photon disponibile su: http://localhost:2322/api"
echo ""
print_info "Esempi di query:"
echo "  • Via Roma 1, Roma"
echo "  • Piazza Duomo, Milano"
echo "  • Corso Vittorio Emanuele 10, Torino"
echo ""
