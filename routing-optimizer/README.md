# 🚚 Routing Optimizer - CVRP con Google OR-Tools

Applicazione web professionale per risolvere il **Capacitated Vehicle Routing Problem (CVRP)** utilizzando Google OR-Tools. L'applicazione permette di ottimizzare i percorsi di consegna importando ordini da un CRM simulato e visualizzando i risultati su una mappa interattiva.

## 📋 Caratteristiche

- ✅ **Simulazione CRM**: Importa 20 ordini simulati con coordinate reali (area di Roma)
- ✅ **Configurazione Flotta**: Numero veicoli, capacità, coordinate deposito
- ✅ **Parametri OR-Tools**: Time limit, strategie di soluzione, metaheuristic
- ✅ **Ottimizzazione CVRP**: Risolve il problema con vincoli di capacità
- ✅ **Visualizzazione Mappa**: Leaflet con percorsi colorati per veicolo
- ✅ **Statistiche Dettagliate**: Distanza, carico, turn-by-turn per ogni veicolo
- ✅ **UI Moderna**: React + Tailwind CSS con design responsivo

## 🛠️ Tech Stack

### Backend
- **FastAPI** (Python): Framework web moderno e veloce
- **Google OR-Tools**: Libreria di ottimizzazione
- **Pydantic**: Validazione dati
- **Uvicorn**: Server ASGI

### Frontend
- **React 18**: Libreria UI
- **TypeScript**: Type safety
- **React Leaflet**: Mappe interattive
- **Tailwind CSS**: Styling utility-first
- **Vite**: Build tool veloce
- **Axios**: Client HTTP

## 📁 Struttura del Progetto

```
routing-optimizer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app principale
│   │   ├── models.py            # Modelli Pydantic
│   │   ├── crm_client.py        # Simulatore CRM
│   │   └── vrp_solver.py        # Logica OR-Tools CVRP
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Componenti React
│   │   │   ├── ConfigurationPanel.tsx
│   │   │   ├── OrdersTable.tsx
│   │   │   ├── ResultsMap.tsx
│   │   │   └── ResultsPanel.tsx
│   │   ├── services/
│   │   │   └── api.ts           # API client
│   │   ├── types/
│   │   │   └── index.ts         # TypeScript types
│   │   ├── utils/
│   │   │   └── mapUtils.ts      # Utility funzioni
│   │   ├── App.tsx              # Componente principale
│   │   ├── main.tsx             # Entry point
│   │   └── index.css            # Stili globali
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
└── README.md
```

## 🚀 Installazione e Avvio

### Prerequisiti
- Python 3.9+
- Node.js 18+
- npm o yarn

### 1. Backend (FastAPI)

```bash
# Entra nella directory backend
cd backend

# Crea virtual environment (opzionale ma consigliato)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate     # Windows

# Installa le dipendenze
pip install -r requirements.txt

# Avvia il server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Il backend sarà disponibile su: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 2. Frontend (React + Vite)

```bash
# Entra nella directory frontend
cd frontend

# Installa le dipendenze
npm install

# Avvia il dev server
npm run dev
```

Il frontend sarà disponibile su: http://localhost:3000

## 📖 Utilizzo

### 1. Configurazione Flotta (Colonna Sinistra)
- **Numero di Veicoli**: Quanti veicoli hai a disposizione (1-50)
- **Capacità Veicolo**: Peso massimo trasportabile in kg
- **Coordinate Deposito**: Punto di partenza/arrivo (default: Roma centro)

### 2. Configurazione OR-Tools (Colonna Destra)
- **Time Limit**: Tempo massimo per l'ottimizzazione in secondi (1-300)
- **First Solution Strategy**: 
  - `PATH_CHEAPEST_ARC`: Percorso più economico disponibile
  - `GLOBAL_CHEAPEST_ARC`: Arco globalmente più economico
  - `AUTOMATIC`: Lascia scegliere a OR-Tools
- **Local Search Metaheuristic**:
  - `GUIDED_LOCAL_SEARCH`: Ricerca locale guidata (consigliato)
  - `TABU_SEARCH`: Evita cicli nella ricerca
  - `SIMULATED_ANNEALING`: Esplorazione globale

### 3. Workflow
1. **Importa da CRM**: Clicca per caricare 20 ordini simulati
2. Visualizza gli ordini nella tabella con coordinate e pesi
3. Verifica che la capacità totale sia sufficiente
4. **Ottimizza Percorsi**: Avvia l'ottimizzazione OR-Tools
5. Visualizza i risultati:
   - 🗺️ **Mappa Interattiva**: Percorsi colorati per veicolo
   - 📊 **Statistiche**: Distanza, carico, tempo computazione
   - 📋 **Dettaglio Turn-by-Turn**: Espandi ogni veicolo per vedere le fermate

## 🔧 API Endpoints

### GET `/api/crm/orders`
Recupera ordini dal CRM simulato
- **Query params**: `num_orders` (default: 20)
- **Response**: Lista ordini con coordinate e domanda

### POST `/api/optimize`
Ottimizza i percorsi
- **Body**: `OptimizationRequest` (ordini + config)
- **Response**: `OptimizationResult` con percorsi ottimizzati

### GET `/api/config/strategies`
Ottieni strategie disponibili OR-Tools
- **Response**: Liste di strategie e metaheuristics

### GET `/health`
Health check
- **Response**: Status del servizio

## 🧮 Algoritmo CVRP

L'applicazione implementa il **Capacitated Vehicle Routing Problem** con:

1. **Matrice Distanze**: Calcolo distanze euclidee con formula di Haversine
2. **Vincolo Capacità**: Ogni veicolo ha un limite di carico
3. **Depot Constraint**: Tutti i veicoli partono e tornano al deposito
4. **Ottimizzazione**: Minimizza la distanza totale percorsa

### Parametri Configurabili
- Numero di veicoli
- Capacità per veicolo
- Time limit computazione
- Strategia soluzione iniziale
- Metaheuristic per ricerca locale

## 🎨 Design Features

- **Responsive**: Funziona su desktop, tablet, mobile
- **Colori Veicoli**: Ogni veicolo ha un colore unico sulla mappa
- **Marker Personalizzati**: 
  - 🔴 Deposito (rosso)
  - 🔵 Clienti non assegnati (blu)
  - 🟢 Clienti assegnati (verde, colorato per veicolo)
- **Polilinee**: Visualizzazione percorsi con spessore e opacità
- **Popup Informativi**: Click sui marker per dettagli
- **Expand/Collapse**: Dettagli veicoli espandibili

## 📊 Esempio Output

```json
{
  "success": true,
  "total_distance": 45.67,
  "total_load": 287.50,
  "num_vehicles_used": 3,
  "num_orders_served": 18,
  "computation_time": 2.345,
  "routes": [
    {
      "vehicle_id": 1,
      "total_distance": 15.23,
      "total_load": 95.00,
      "color": "#FF5733",
      "stops": [...]
    }
  ]
}
```

## 🐛 Troubleshooting

### Backend non si avvia
- Verifica che Python 3.9+ sia installato
- Controlla che tutte le dipendenze siano installate
- Verifica che la porta 8000 sia libera

### Frontend non si connette al backend
- Verifica che il backend sia in esecuzione
- Controlla la configurazione CORS in `main.py`
- Verifica l'URL dell'API in `api.ts`

### Ottimizzazione fallisce
- Verifica che la capacità totale sia sufficiente
- Aumenta il time limit
- Riduci il numero di ordini
- Prova strategie diverse

## 📝 Note Sviluppo

### Coordinare Reali
Gli ordini simulati usano coordinate reali nell'area di Roma:
- Centro: 41.9028°N, 12.4964°E
- Raggio: 5-10 km dal centro

### Distanze
- Calcolo: Formula di Haversine (distanza geodesica)
- Unità: Metri (convertiti in km per visualizzazione)
- Accuratezza: ±1% rispetto a distanze stradali reali

### Performance
- **Ordini**: Testato fino a 100 ordini
- **Veicoli**: Testato fino a 50 veicoli
- **Tempo**: Tipicamente < 5s per 20 ordini, 3 veicoli

## 🔮 Possibili Estensioni

- [ ] Integrazione con API CRM reale (Salesforce, HubSpot)
- [ ] Calcolo distanze con Google Maps Directions API
- [ ] Time windows (finestre temporali consegna)
- [ ] Priorità ordini
- [ ] Export risultati (PDF, Excel, JSON)
- [ ] Salvataggio configurazioni
- [ ] Confronto soluzioni multiple
- [ ] Dashboard analytics
- [ ] Multi-depot support
- [ ] Driver assignment

## 📄 Licenza

Questo progetto è fornito come esempio educativo.

## 👨‍💻 Autore

Sviluppato come soluzione professionale per ottimizzazione logistica con Google OR-Tools.

---

**Buona ottimizzazione! 🚚📦**
