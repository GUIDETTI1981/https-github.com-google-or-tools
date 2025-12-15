#!/bin/bash

# Script di avvio servizi per Sistema Gestione Ritiri con OR-Tools
# 
# Uso: ./start_services.sh

echo "======================================================================="
echo "🚀 Sistema Gestione Ritiri con OR-Tools"
echo "======================================================================="
echo ""

# Colori
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directory di lavoro
cd "$(dirname "$0")"

# Verifica dipendenze Python
echo -e "${YELLOW}📦 Verifica dipendenze Python...${NC}"
if ! python -c "import ortools" &> /dev/null; then
    echo -e "${RED}❌ OR-Tools non installato${NC}"
    echo "Installazione dipendenze..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Errore installazione dipendenze${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ Dipendenze OK${NC}"
echo ""

# Kill processi esistenti
echo -e "${YELLOW}🔄 Terminazione processi esistenti...${NC}"
pkill -f "python api.py" &> /dev/null
pkill -f "python.*http.server.*8000" &> /dev/null
sleep 1

# Avvio API Backend
echo -e "${YELLOW}🚀 Avvio API Backend (porta 5000)...${NC}"
nohup python api.py > /tmp/ortools_api.log 2>&1 &
API_PID=$!
sleep 3

# Verifica API
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API Backend attiva (PID: $API_PID)${NC}"
else
    echo -e "${RED}❌ Errore avvio API Backend${NC}"
    echo "Controlla il log: tail -f /tmp/ortools_api.log"
    exit 1
fi
echo ""

# Avvio Frontend
echo -e "${YELLOW}🌐 Avvio Frontend (porta 8000)...${NC}"
nohup python -m http.server 8000 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 2

# Verifica Frontend
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend attivo (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}❌ Errore avvio Frontend${NC}"
    echo "Controlla il log: tail -f /tmp/frontend.log"
    exit 1
fi
echo ""

# Riepilogo
echo "======================================================================="
echo -e "${GREEN}✅ Tutti i servizi sono attivi!${NC}"
echo "======================================================================="
echo ""
echo "📍 URL Servizi:"
echo "   Frontend:     http://localhost:8000"
echo "   API Backend:  http://localhost:5000"
echo "   Health Check: http://localhost:5000/health"
echo ""
echo "📝 Log:"
echo "   API:      tail -f /tmp/ortools_api.log"
echo "   Frontend: tail -f /tmp/frontend.log"
echo ""
echo "🛑 Per fermare i servizi:"
echo "   pkill -f 'python api.py'"
echo "   pkill -f 'python.*http.server.*8000'"
echo ""
echo "🧪 Test integrazione:"
echo "   python test_integration.py"
echo ""
echo "======================================================================="
echo -e "${GREEN}Sistema pronto all'uso! 🎉${NC}"
echo "======================================================================="
