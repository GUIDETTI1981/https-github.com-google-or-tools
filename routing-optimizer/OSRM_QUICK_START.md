# 🚀 OSRM Quick Start - 5 Minuti

## Setup Rapido OSRM per Distanze Stradali Reali

### Step 1: Download e Preprocessing Mappe (10-15 min, una tantum)

```bash
cd routing-optimizer
./init_osrm.sh
```

**Questo comando:**
- Scarica mappa Italia da OpenStreetMap (~500 MB)
- Processa la mappa per OSRM (Extract → Partition → Customize)
- Salva dati ottimizzati in `./osrm-data/`

**Tempo:** ~10-15 minuti la prima volta, poi mai più!

---

### Step 2: Avvia OSRM Server (10 secondi)

```bash
docker-compose up osrm
```

**Output atteso:**
```
osrm  | [info] starting up engines, v5.27.1
osrm  | [info] Threads: 8
osrm  | [info] IP address: 0.0.0.0
osrm  | [info] IP port: 5000
osrm  | [info] http 1.1 compression handled by zlib version 1.2.11
osrm  | [info] running and waiting for requests
```

---

### Step 3: Verifica OSRM (5 secondi)

```bash
curl "http://localhost:5000/route/v1/driving/12.4964,41.9028;12.5,41.91?overview=false"
```

**Output atteso:**
```json
{
  "code": "Ok",
  "routes": [{
    "distance": 1234.5,
    "duration": 67.8
  }]
}
```

✅ **Se vedi questo, OSRM funziona!**

---

### Step 4: Avvia Backend con OSRM (5 secondi)

```bash
# Opzione A: Solo backend
docker-compose up backend

# Opzione B: Tutti i servizi
docker-compose up
```

**Verifica nei log:**
```
INFO: 🚗 Modalità OSRM attiva - Usando distanze stradali reali
INFO: ✅ Matrici OSRM calcolate: 21x21
```

---

### Step 5: Test Ottimizzazione (2-5 secondi)

```bash
curl -X POST http://localhost:8000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "orders": [...],
    "fleet_config": {...},
    "ortools_config": {...}
  }'
```

Guarda il messaggio nel risultato:
```json
{
  "success": true,
  "message": "Ottimizzazione completata con successo (OSRM)",
  ...
}
```

✅ **"(OSRM)" significa che stai usando distanze reali!**

---

## 🎯 Differenza OSRM vs Haversine

### Con Haversine (distanza aerea):
```
Deposito → Cliente A: 5.2 km (linea retta)
Distanza totale: 45.6 km
```

### Con OSRM (distanza stradale):
```
Deposito → Cliente A: 7.8 km (seguendo strade)
Distanza totale: 63.4 km (+39% più realistico!)
```

---

## ⚙️ Comandi Utili

### Verifica Status OSRM
```bash
curl http://localhost:8000/api/osrm/status
```

### Disabilita OSRM (torna a Haversine)
```bash
# In docker-compose.yml, cambia:
environment:
  - USE_OSRM=false

# Poi riavvia:
docker-compose restart backend
```

### Riabilita OSRM
```bash
# In docker-compose.yml, cambia:
environment:
  - USE_OSRM=true

# Poi riavvia:
docker-compose restart backend
```

### Stop servizi
```bash
docker-compose down
```

### Restart OSRM solo
```bash
docker-compose restart osrm
```

---

## 🗺️ Mappe Alternative

### Solo Roma e Lazio (più piccola, più veloce)
```bash
./init_osrm.sh lazio
```

### Italia Centrale
```bash
./init_osrm.sh central-italy
```

### Italia Completa (default)
```bash
./init_osrm.sh italy
```

---

## 📊 Performance OSRM

| Ordini | Tempo Calcolo Matrice | Note |
|--------|----------------------|------|
| 5 | ~50ms | Velocissimo |
| 20 | ~200ms | Ottimale |
| 50 | ~500ms | Buono |
| 100 | ~2s | Limite consigliato |

---

## 🐛 Problemi Comuni

### "osrm: Cannot start"
**Soluzione:**
```bash
# Re-processa mappe
./init_osrm.sh

# Verifica file
ls -lh osrm-data/*.osrm*
```

### "OSRM timeout"
**Soluzione:**
```bash
# Riduci numero ordini o aumenta timeout
# In osrm_client.py, timeout default è 30s
```

### "Host osrm not found"
**Soluzione:**
```bash
# Usa docker-compose (con hyphen), non docker compose
docker-compose up
```

---

## ✅ Checklist Setup

- [ ] Docker installato
- [ ] `./init_osrm.sh` eseguito con successo
- [ ] Folder `osrm-data/` contiene file `.osrm*`
- [ ] `docker-compose up osrm` avviato
- [ ] Test curl OSRM OK
- [ ] Backend avviato con log "Modalità OSRM attiva"
- [ ] Ottimizzazione test completata

---

## 📚 Documentazione Completa

Leggi `OSRM_INTEGRATION.md` per:
- Architettura dettagliata
- API reference completo
- Troubleshooting avanzato
- Performance tuning
- Estensioni future

---

**Setup completato in 5 minuti! 🎉**

🗺️ **Ora hai distanze stradali reali!** 🚗
