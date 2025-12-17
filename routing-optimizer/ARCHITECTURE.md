# 🏗️ Architettura - Routing Optimizer

## Panoramica Sistema

Routing Optimizer è un'applicazione web full-stack per risolvere il **Capacitated Vehicle Routing Problem (CVRP)** utilizzando Google OR-Tools.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT BROWSER                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           React Frontend (TypeScript + Tailwind)          │  │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │  │
│  │  │  Config │  │  Orders  │  │   Map    │  │  Results  │  │  │
│  │  │  Panel  │  │  Table   │  │ (Leaflet)│  │   Panel   │  │  │
│  │  └─────────┘  └──────────┘  └──────────┘  └───────────┘  │  │
│  └───────────────────────┬──────────────────────────────────┘  │
└────────────────────────────┼──────────────────────────────────┘
                             │ HTTP/REST (Axios)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                        API Layer                          │  │
│  │  /api/crm/orders | /api/optimize | /api/config/strategies│  │
│  └────────────┬───────────────┬──────────────────────────────┘  │
│               │               │                                  │
│  ┌────────────▼─────────┐  ┌─▼──────────────────────────────┐  │
│  │    CRMClient         │  │     VRPSolver                  │  │
│  │  (Data Simulation)   │  │  (OR-Tools CVRP Logic)         │  │
│  │                      │  │                                │  │
│  │ - Generate Orders    │  │ - Distance Matrix (Haversine) │  │
│  │ - Roma Coordinates   │  │ - Routing Index Manager       │  │
│  │ - Realistic Demands  │  │ - Capacity Constraints        │  │
│  └──────────────────────┘  │ - First Solution Strategy     │  │
│                             │ - Local Search Metaheuristic  │  │
│                             │ - Route Extraction            │  │
│                             └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Componenti Principali

### 🎨 Frontend (React + TypeScript)

#### 1. **App.tsx** - Componente Principale
- Gestisce lo stato globale dell'applicazione
- Coordina il flusso tra componenti
- Gestisce chiamate API e stati di caricamento

#### 2. **ConfigurationPanel.tsx**
**Responsabilità:**
- Input configurazione flotta (veicoli, capacità, deposito)
- Input parametri OR-Tools (time limit, strategie)
- Validazione capacità totale vs domanda totale
- Trigger azioni: Import CRM, Ottimizzazione

**State Management:**
```typescript
- numVehicles: number
- vehicleCapacity: number
- depotLat/depotLon: number
- timeLimit: number
- firstSolutionStrategy: string
- localSearchMetaheuristic: string
```

#### 3. **OrdersTable.tsx**
**Responsabilità:**
- Visualizzazione tabellare ordini importati
- Statistiche aggregate (peso totale)
- Scrolling per liste lunghe

#### 4. **ResultsMap.tsx** (React Leaflet)
**Responsabilità:**
- Rendering mappa OpenStreetMap
- Marker deposito (rosso)
- Marker clienti (blu/verde)
- Polilinee percorsi (colorate per veicolo)
- Popup informativi interattivi

**Layers:**
1. TileLayer (OpenStreetMap)
2. Depot Marker + Circle
3. Customer Markers
4. Route Polylines
5. Popups

#### 5. **ResultsPanel.tsx**
**Responsabilità:**
- Statistiche aggregate ottimizzazione
- Dettaglio turn-by-turn per veicolo
- UI espandibile per percorsi
- Suggerimenti utente

### ⚙️ Backend (FastAPI + OR-Tools)

#### 1. **main.py** - FastAPI Application
**Endpoints:**

```python
GET  /                         # Info API
GET  /health                   # Health check
GET  /api/crm/orders           # Import ordini CRM
POST /api/optimize             # Ottimizza percorsi
GET  /api/config/strategies    # Strategie disponibili
```

**Middleware:**
- CORS (per frontend)
- JSON validation (Pydantic)
- Error handling
- Logging

#### 2. **models.py** - Pydantic Models
**Data Models:**
- `Order`: Ordine singolo (id, nome, coordinate, domanda)
- `DepotLocation`: Coordinate deposito
- `FleetConfiguration`: Config flotta
- `ORToolsConfiguration`: Parametri algoritmo
- `OptimizationRequest`: Richiesta completa
- `RouteStop`: Fermata in percorso
- `VehicleRoute`: Percorso completo veicolo
- `OptimizationResult`: Risultato ottimizzazione

**Validazione Automatica:**
- Range check (lat/lon, capacità, ecc.)
- Type safety
- Default values

#### 3. **crm_client.py** - CRM Simulator
**Classe: CRMClient**

**Metodi Principali:**
```python
get_orders(num_orders: int) -> CRMOrdersResponse
    # Genera ordini simulati con coordinate Roma
    
_generate_realistic_coordinates(num_points: int) -> List[tuple]
    # Genera punti entro raggio 5-10km da centro Roma
    # Usa distribuzione casuale angolare
    
validate_orders(orders: List[Order]) -> dict
    # Valida coordinate e domande
```

**Dati Simulati:**
- 24 nomi clienti italiani realistici
- Coordinate area Roma (41.90°N, 12.50°E)
- Domande casuali 5-50 kg
- ID sequenziali (ORD0001, ORD0002, ...)

#### 4. **vrp_solver.py** - OR-Tools CVRP Solver
**Classe: VRPSolver**

**Pipeline di Ottimizzazione:**

```
1. Inizializzazione
   └─> Parsing richiesta
   └─> Creazione lista locazioni (depot + orders)
   └─> Preparazione demands

2. Calcolo Matrice Distanze
   └─> Haversine distance per ogni coppia
   └─> Conversione metri → interi (OR-Tools requirement)

3. Setup OR-Tools
   └─> RoutingIndexManager (gestione indici)
   └─> RoutingModel (modello problema)

4. Registrazione Callbacks
   └─> Distance Callback (matrice distanze)
   └─> Demand Callback (capacità)

5. Aggiunta Vincoli
   └─> Dimensione Capacity (demand + vehicle_capacity)

6. Configurazione Ricerca
   └─> First Solution Strategy
   └─> Local Search Metaheuristic
   └─> Time Limit

7. Risoluzione
   └─> SolveWithParameters()

8. Estrazione Risultati
   └─> Parsing solution
   └─> Costruzione VehicleRoute objects
   └─> Calcolo statistiche
```

**Algoritmo Distanze - Haversine:**
```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Raggio Terra in metri
    
    # Conversione gradi → radianti
    φ1, φ2 = radians(lat1), radians(lat2)
    Δφ = radians(lat2 - lat1)
    Δλ = radians(lon2 - lon1)
    
    # Formula Haversine
    a = sin²(Δφ/2) + cos(φ1) * cos(φ2) * sin²(Δλ/2)
    c = 2 * atan2(√a, √(1-a))
    
    distance = R * c
    return distance
```

## Flusso Dati

### 1️⃣ Import Ordini CRM

```
User Click "Importa da CRM"
    │
    ├─> Frontend: handleImportOrders()
    │       │
    │       ├─> API Call: GET /api/crm/orders?num_orders=20
    │       │
    ├─> Backend: get_crm_orders()
    │       │
    │       ├─> CRMClient.get_orders(20)
    │       │       │
    │       │       ├─> Genera coordinate Roma
    │       │       ├─> Seleziona nomi clienti
    │       │       ├─> Genera domande casuali
    │       │       └─> Crea Order objects
    │       │
    │       └─> Return CRMOrdersResponse
    │
    └─> Frontend: setState(orders)
            │
            └─> Render OrdersTable + Map (markers)
```

### 2️⃣ Ottimizzazione Percorsi

```
User Click "Ottimizza Percorsi"
    │
    ├─> Frontend: handleOptimize()
    │       │
    │       ├─> Costruisci OptimizationRequest
    │       │   ├─> orders: Order[]
    │       │   ├─> fleet_config: FleetConfiguration
    │       │   └─> ortools_config: ORToolsConfiguration
    │       │
    │       ├─> API Call: POST /api/optimize
    │       │
    ├─> Backend: optimize_routes()
    │       │
    │       ├─> Validazioni iniziali
    │       │
    │       ├─> VRPSolver.solve()
    │       │       │
    │       │       ├─> 1. compute_euclidean_distance_matrix()
    │       │       │       └─> Haversine per tutte le coppie
    │       │       │
    │       │       ├─> 2. Setup OR-Tools
    │       │       │       ├─> RoutingIndexManager
    │       │       │       ├─> RoutingModel
    │       │       │       ├─> Distance Callback
    │       │       │       ├─> Demand Callback
    │       │       │       └─> Capacity Dimension
    │       │       │
    │       │       ├─> 3. Configurazione Search Parameters
    │       │       │       ├─> First Solution Strategy
    │       │       │       ├─> Local Search Metaheuristic
    │       │       │       └─> Time Limit
    │       │       │
    │       │       ├─> 4. Solve (OR-Tools magic! 🎩✨)
    │       │       │
    │       │       └─> 5. Extract Routes
    │       │               ├─> Per ogni veicolo:
    │       │               │   ├─> Segui nextVar chain
    │       │               │   ├─> Crea RouteStop objects
    │       │               │   ├─> Calcola distanza totale
    │       │               │   └─> Calcola carico cumulativo
    │       │               │
    │       │               └─> Return VehicleRoute[]
    │       │
    │       └─> Return OptimizationResult
    │
    └─> Frontend: setState(result)
            │
            └─> Render Results
                ├─> ResultsMap: Polilinee colorate + markers
                └─> ResultsPanel: Statistiche + dettagli
```

## Strategie OR-Tools

### First Solution Strategies

1. **PATH_CHEAPEST_ARC** ⭐ (Default)
   - Costruisce percorsi scegliendo sempre l'arco più economico disponibile
   - Veloce e produce soluzioni decenti
   - Buono per problemi di medie dimensioni

2. **GLOBAL_CHEAPEST_ARC**
   - Considera globalmente l'arco più economico
   - Più lento ma potenzialmente migliori soluzioni iniziali
   - Utile quando la qualità iniziale è critica

3. **AUTOMATIC**
   - OR-Tools sceglie automaticamente la strategia
   - Adattivo al problema specifico

### Local Search Metaheuristics

1. **GUIDED_LOCAL_SEARCH** ⭐ (Default)
   - Penalizza soluzioni già visitate
   - Buon bilanciamento qualità/tempo
   - Consigliato per la maggior parte dei casi

2. **TABU_SEARCH**
   - Mantiene lista di mosse "tabù"
   - Evita cicli nella ricerca
   - Buono per sfuggire ottimi locali

3. **SIMULATED_ANNEALING**
   - Accetta soluzioni peggiori con probabilità decrescente
   - Esplorazione più globale
   - Può trovare soluzioni migliori ma più lento

## Performance & Scaling

### Complessità
- **CVRP**: NP-Hard
- **Complessità teorica**: O(n! * m) dove n=ordini, m=veicoli
- **OR-Tools**: Usa euristiche per scalare

### Limiti Pratici
| Parametro | Min | Max | Raccomandato |
|-----------|-----|-----|--------------|
| Ordini    | 1   | 100 | 20-50        |
| Veicoli   | 1   | 50  | 3-10         |
| Time Limit| 1s  | 300s| 30-60s       |

### Tempo Computazione (circa)
- 20 ordini, 3 veicoli: **< 5 secondi**
- 50 ordini, 5 veicoli: **10-30 secondi**
- 100 ordini, 10 veicoli: **60-120 secondi**

## Sicurezza

### Backend
- ✅ Input validation (Pydantic)
- ✅ CORS configurato
- ✅ Rate limiting (consigliato in produzione)
- ✅ Error handling robusto

### Frontend
- ✅ Type safety (TypeScript)
- ✅ Input sanitization
- ✅ Timeout HTTP requests (2 minuti)
- ✅ Error boundaries (React)

## Estensibilità

### Backend
```python
# Esempio: Integrazione CRM reale
class RealCRMClient(CRMClient):
    def get_orders(self, num_orders: int):
        response = requests.get(
            f"{CRM_API_URL}/orders",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        return self._parse_crm_response(response.json())
```

### Frontend
```typescript
// Esempio: Export risultati PDF
const exportToPDF = async (result: OptimizationResult) => {
  const doc = new jsPDF();
  // ... formato PDF
  doc.save('routing-result.pdf');
};
```

## Testing

### Backend
```bash
cd backend
pytest tests/
```

### Frontend
```bash
cd frontend
npm run test
```

## Deployment

### Backend (Production)
```bash
# Con Gunicorn + Uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Frontend (Build)
```bash
cd frontend
npm run build
# Output in dist/
```

### Docker (Opzionale)
```dockerfile
# Backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]

# Frontend
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "run", "preview"]
```

---

**Architettura progettata per scalabilità, manutenibilità ed estensibilità.** 🏗️
