# 🗺️ Integrazione OSRM - Distanze Stradali Reali

## 📋 Panoramica

Questa guida documenta l'integrazione di **OSRM (Open Source Routing Machine)** nel Routing Optimizer per sostituire le distanze euclidee (Haversine) con **distanze e tempi di percorrenza stradali reali**.

### Vantaggi OSRM
✅ **Distanze reali**: Percorsi stradali effettivi, non linea d'aria  
✅ **Tempi accurati**: Durata percorrenza considerando velocità strade  
✅ **Self-hosted**: Nessuna dipendenza da servizi esterni  
✅ **Gratuito**: Basato su dati OpenStreetMap  
✅ **Veloce**: Algoritmo MLD ottimizzato per query multiple  

---

## 🏗️ Architettura

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                         │
│  ┌────────────┐        ┌──────────────┐                    │
│  │ VRP Solver │───────▶│ OSRM Client  │                    │
│  │  (OR-Tools)│        │  (Python)    │                    │
│  └────────────┘        └──────┬───────┘                    │
└────────────────────────────────┼──────────────────────────┘
                                 │ HTTP Request
                                 │ Table API
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  OSRM Backend (Docker)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Pre-processed Map Data (italy-latest.osrm)         │  │
│  │  - Extract  - Partition  - Customize (MLD)          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Algorithm: Multi-Level Dijkstra (MLD)                     │
│  Port: 5000                                                 │
│  API: /table/v1/driving/coords?annotations=distance,duration│
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Setup e Installazione

### Prerequisiti
- Docker installato
- ~2-5 GB spazio disco (per mappe Italia)
- Connessione internet (per download mappe)

### Step 1: Download e Preprocessing Mappe

Esegui lo script automatizzato:

```bash
cd routing-optimizer
./init_osrm.sh
```

**Cosa fa lo script:**
1. Scarica mappa OpenStreetMap da Geofabrik (es. italy-latest.osm.pbf)
2. Extract: Estrae grafo stradale (~2-5 min)
3. Partition: Partiziona grafo per MLD (~1-3 min)
4. Customize: Ottimizza per query veloci (~1-3 min)
5. Salva files processati in `./osrm-data/`

**Tempo totale:** ~5-15 minuti (dipende da CPU e dimensione mappa)

**Opzioni regionali:**
```bash
./init_osrm.sh italy          # Italia completa (~500 MB)
./init_osrm.sh central-italy  # Italia centrale (~200 MB)
./init_osrm.sh lazio          # Solo Lazio (~50 MB)
./init_osrm.sh rome           # Alias per central-italy
```

### Step 2: Avvia OSRM Server

**Opzione A: Solo OSRM**
```bash
docker-compose up osrm
```

**Opzione B: Tutti i servizi**
```bash
docker-compose up
```

**Verifica OSRM:**
```bash
curl "http://localhost:5000/route/v1/driving/12.4964,41.9028;12.5,41.91?overview=false"
```

Output atteso:
```json
{
  "code": "Ok",
  "routes": [{
    "distance": 1234.5,
    "duration": 67.8
  }]
}
```

---

## 📚 Componenti Implementati

### 1️⃣ Docker Compose (`docker-compose.yml`)

**Servizio OSRM configurato:**
```yaml
osrm:
  image: osrm/osrm-backend:latest
  ports:
    - "5000:5000"
  volumes:
    - ./osrm-data:/data
  command: osrm-routed --algorithm mld /data/italy-latest.osrm --max-table-size 10000
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**Parametri chiave:**
- `--algorithm mld`: Multi-Level Dijkstra (veloce per matrici)
- `--max-table-size 10000`: Supporta fino a 100x100 locations
- Volume mount: Mappa pre-processata persistente

### 2️⃣ OSRM Client Python (`backend/app/services/osrm_client.py`)

**Classe principale:**
```python
from app.services.osrm_client import OSRMClient

# Inizializza client
osrm = OSRMClient(host='localhost', port=5000)

# Health check
is_ok = osrm.health_check()

# Ottieni matrici distanze/tempi
coordinates = [(41.9028, 12.4964), (41.91, 12.5), ...]
distance_matrix, duration_matrix = osrm.get_matrix(coordinates)
# distance_matrix: List[List[int]] - metri
# duration_matrix: List[List[int]] - secondi
```

**Features:**
- ✅ Gestione errori robusta
- ✅ Fallback automatico a Haversine se OSRM non disponibile
- ✅ Conversione automatica in interi per OR-Tools
- ✅ Arrotondamento per eccesso (evita sottostime)
- ✅ Gestione percorsi impossibili (valore alto 999999999)

### 3️⃣ VRP Solver con OSRM (`backend/app/vrp_solver_osrm.py`)

**Nuovo solver integrato:**
```python
from app.vrp_solver_osrm import VRPSolverOSRM

# Crea solver
solver = VRPSolverOSRM(
    request=optimization_request,
    use_osrm=True  # True = OSRM, False = Haversine
)

# Risolvi
result = solver.solve()
```

**Logica intelligente:**
1. Tenta connessione OSRM
2. Se OK: usa distanze stradali reali
3. Se fallisce: fallback automatico a Haversine
4. Logging chiaro di quale metodo è usato

### 4️⃣ API Endpoints Aggiornati

**Nuovo endpoint verifica OSRM:**
```bash
GET /api/osrm/status
```

**Response:**
```json
{
  "status": "available",
  "enabled": true,
  "host": "osrm",
  "port": 5000,
  "base_url": "http://osrm:5000",
  "is_available": true,
  "message": "OSRM is operational"
}
```

**Endpoint esistente aggiornato:**
```bash
GET /api/stats
```

**Response (con OSRM info):**
```json
{
  "crm_available": true,
  "ortools_version": "9.8.3296",
  "osrm_enabled": true,
  "osrm_available": true,
  "osrm_info": {
    "host": "osrm",
    "port": 5000,
    "base_url": "http://osrm:5000",
    "profile": "driving"
  }
}
```

---

## ⚙️ Configurazione

### Variabili d'Ambiente

**Backend (`docker-compose.yml` o `.env`):**
```bash
# OSRM Configuration
OSRM_HOST=osrm           # Hostname container OSRM
OSRM_PORT=5000           # Porta OSRM
USE_OSRM=true            # true = OSRM, false = Haversine

# Python Configuration
PYTHONUNBUFFERED=1
```

**Frontend:**
```bash
VITE_API_BASE_URL=http://backend:8000
```

### Disabilitare OSRM

Se vuoi tornare a Haversine temporaneamente:

```bash
# Nel docker-compose.yml
environment:
  - USE_OSRM=false
```

Oppure:
```bash
export USE_OSRM=false
docker-compose up
```

---

## 🧪 Testing

### Test 1: Health Check OSRM
```bash
curl http://localhost:5000/route/v1/driving/12.4964,41.9028;12.5,41.91
```

### Test 2: Verifica Status da Backend
```bash
curl http://localhost:8000/api/osrm/status
```

### Test 3: Ottimizzazione Completa
```bash
curl -X POST http://localhost:8000/api/optimize \
  -H "Content-Type: application/json" \
  -d @test_optimization.json
```

Verifica nel log:
```
INFO: 🚗 Modalità OSRM attiva - Usando distanze stradali reali
INFO: ✅ Matrici OSRM calcolate: 21x21
INFO: Ottimizzazione completata con successo (OSRM)
```

### Test 4: Comparazione OSRM vs Haversine

**Con OSRM:**
```bash
USE_OSRM=true docker-compose up backend
# Ottimizza e nota: distanza totale X km
```

**Con Haversine:**
```bash
USE_OSRM=false docker-compose up backend
# Ottimizza e nota: distanza totale Y km
```

**Differenza tipica:** OSRM ~20-40% più lungo (percorsi stradali vs linea d'aria)

---

## 📊 Performance

### Benchmark Tipici

| Locations | OSRM (MLD) | Haversine | Note |
|-----------|------------|-----------|------|
| 5 | ~50ms | ~2ms | OSRM overhead iniziale |
| 20 | ~200ms | ~5ms | Accettabile |
| 50 | ~500ms | ~15ms | Ancora buono |
| 100 | ~2s | ~50ms | Limite consigliato |

**Raccomandazioni:**
- **< 50 locations**: OSRM perfetto
- **50-100 locations**: OSRM OK, considera caching
- **> 100 locations**: Considera clustering o batch processing

### Ottimizzazioni Possibili

1. **Caching matrici**: Salva matrici calcolate per riutilizzo
2. **Warm-up**: Pre-calcola matrici comuni all'avvio
3. **Clustering**: Dividi problemi grandi in sub-problemi
4. **Profilo alternativo**: `walking` o `cycling` se appropriato

---

## 🐛 Troubleshooting

### Problema: OSRM non si avvia

**Sintomi:**
```
ERROR: Cannot start service osrm
```

**Soluzioni:**
1. Verifica che mappe siano processate:
   ```bash
   ls -lh osrm-data/*.osrm*
   ```
2. Re-esegui preprocessing:
   ```bash
   ./init_osrm.sh
   ```
3. Verifica logs:
   ```bash
   docker-compose logs osrm
   ```

### Problema: "OSRM timeout"

**Cause:**
- Server OSRM sovraccarico
- Query troppo grande (>100 locations)
- Rete lenta

**Soluzioni:**
1. Aumenta timeout in `osrm_client.py`:
   ```python
   osrm = OSRMClient(timeout=60)  # 60 secondi
   ```
2. Riduci numero locations
3. Verifica `max-table-size` in docker-compose.yml

### Problema: "Host osrm not found"

**Causa:** Backend non riesce a risolvere hostname `osrm`

**Soluzioni:**
1. Verifica network Docker:
   ```bash
   docker network inspect routing-optimizer_routing-network
   ```
2. Usa `docker-compose` non `docker compose` (underscore vs hyphen)
3. Verifica `depends_on` in docker-compose.yml

### Problema: Distanze molto diverse da attese

**Causa:** Coordinate invertite (lat/lon vs lon/lat)

**Verifica:** OSRM usa `lon,lat` (non `lat,lon`)

**Soluzione:** Il client gestisce già la conversione automaticamente:
```python
# Input: (lat, lon)
coordinates = [(41.9028, 12.4964), ...]
# Converte internamente in: lon,lat per OSRM
```

---

## 🔮 Estensioni Future

### Possibili Miglioramenti

1. **Time Windows con durata reale**
   - Usa `duration_matrix` per vincoli temporali
   - Ottimizza per tempo invece di distanza

2. **Multi-profilo**
   - `driving`: Auto
   - `walking`: Pedoni
   - `cycling`: Biciclette

3. **Avoid features**
   - Evita autostrade
   - Evita pedaggi
   - Preferenze strade

4. **Turn-by-turn navigation**
   - Usa `/route` endpoint per geometria dettagliata
   - Esporta GPX per navigatori

5. **Traffic integration**
   - Dati traffico real-time (richiede OSRM modificato)

---

## 📖 Risorse

### Documentazione
- **OSRM Project**: https://project-osrm.org/
- **OSRM API Docs**: http://project-osrm.org/docs/v5.24.0/api/
- **Geofabrik Downloads**: https://download.geofabrik.de/
- **OpenStreetMap**: https://www.openstreetmap.org/

### File Progetto
- `docker-compose.yml`: Configurazione servizi
- `init_osrm.sh`: Script preprocessing mappe
- `backend/app/services/osrm_client.py`: Client Python
- `backend/app/vrp_solver_osrm.py`: Solver integrato
- `backend/Dockerfile`: Container backend
- `backend/requirements.txt`: Dipendenze (include `requests`)

---

## ✅ Checklist Implementazione

### Infrastruttura
- [x] `docker-compose.yml` con servizio OSRM
- [x] Volume mount `./osrm-data`
- [x] Porta 5000 esposta
- [x] Algoritmo MLD configurato
- [x] Health check OSRM
- [x] Network Docker condiviso

### Script Setup
- [x] `init_osrm.sh` eseguibile
- [x] Download mappe Geofabrik
- [x] Extract pipeline
- [x] Partition pipeline
- [x] Customize pipeline
- [x] Gestione errori
- [x] Output colorato
- [x] Cleanup opzionale

### Client Python
- [x] `osrm_client.py` implementato
- [x] Classe `OSRMClient`
- [x] Metodo `get_matrix()` con annotazioni
- [x] Conversione int per OR-Tools
- [x] Arrotondamento per eccesso
- [x] Gestione percorsi impossibili
- [x] Health check
- [x] Gestione eccezioni `OSRMClientError`
- [x] Timeout configurabile
- [x] Logging strutturato

### Integrazione Solver
- [x] `vrp_solver_osrm.py` creato
- [x] Fallback automatico Haversine
- [x] Flag `use_osrm` configurabile
- [x] Integrazione matrice distanze
- [x] Integrazione matrice durate
- [x] Logging metodo usato
- [x] Compatibilità API esistente

### API Backend
- [x] Import `OSRMClient` e `VRPSolverOSRM`
- [x] Variabile env `USE_OSRM`
- [x] Switch dinamico solver
- [x] Endpoint `/api/osrm/status`
- [x] Aggiornamento `/api/stats`
- [x] `requests` in `requirements.txt`

### Testing
- [x] Health check OSRM
- [x] Test Table API
- [x] Test ottimizzazione completa
- [x] Verifica fallback Haversine
- [x] Comparazione distanze

### Documentazione
- [x] `OSRM_INTEGRATION.md` completo
- [x] Architettura diagrammata
- [x] Setup guide step-by-step
- [x] Troubleshooting section
- [x] Performance benchmarks
- [x] Esempi codice

---

## 🎉 Conclusioni

OSRM è stato **integrato con successo** nel Routing Optimizer, fornendo:

✅ **Distanze reali** basate su rete stradale  
✅ **Tempi accurati** di percorrenza  
✅ **Fallback robusto** a Haversine se necessario  
✅ **Self-hosted** senza dipendenze esterne  
✅ **Performance eccellenti** con algoritmo MLD  

L'integrazione è **production-ready** e pronta all'uso!

---

**Developed with ❤️ for accurate routing optimization**

🗺️ **Happy Routing!** 🚗
