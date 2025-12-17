#!/bin/bash

# Script di avvio per Routing Optimizer
# Avvia backend (FastAPI) e frontend (Vite) in parallelo

echo "🚀 Avvio Routing Optimizer..."
echo ""

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funzione per gestire l'interruzione (Ctrl+C)
cleanup() {
    echo -e "\n${RED}🛑 Interruzione ricevuta. Chiusura servizi...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Verifica dipendenze Python
echo -e "${BLUE}📦 Verifica dipendenze backend...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creazione virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate 2>/dev/null || . venv/bin/activate

echo -e "${BLUE}Installazione dipendenze Python...${NC}"
pip install -q -r requirements.txt

# Avvia backend
echo -e "${GREEN}🐍 Avvio Backend FastAPI su porta 8000...${NC}"
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..

sleep 3

# Verifica dipendenze Node
echo -e "${BLUE}📦 Verifica dipendenze frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installazione dipendenze Node.js...${NC}"
    npm install
fi

# Avvia frontend
echo -e "${GREEN}⚛️  Avvio Frontend React su porta 3000...${NC}"
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}✅ Servizi avviati con successo!${NC}"
echo ""
echo -e "${BLUE}📍 Backend API:${NC}  http://localhost:8000"
echo -e "${BLUE}📍 API Docs:${NC}     http://localhost:8000/docs"
echo -e "${BLUE}📍 Frontend:${NC}     http://localhost:3000"
echo ""
echo -e "${BLUE}Premi Ctrl+C per fermare tutti i servizi${NC}"
echo ""

# Mantieni lo script in esecuzione
wait
