# 🌐 Accesso Applicazione - Routing Optimizer

## ✅ Applicazione Live e Funzionante

**Data**: 2025-12-17  
**Status**: 🟢 **OPERATIVO**

---

## 🚀 URL Accesso Immediato

### 📱 Frontend (Interfaccia Utente)
**Applicazione Web React:**
```
https://3001-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai
```
👉 **Clicca qui per accedere:** https://3001-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai

**Features:**
- ✅ Configurazione flotta e parametri OR-Tools
- ✅ Import ordini da CRM simulato
- ✅ Visualizzazione ordini in tabella
- ✅ Mappa interattiva Leaflet
- ✅ Ottimizzazione percorsi CVRP
- ✅ Dashboard risultati con statistiche
- ✅ Dettaglio turn-by-turn per veicolo

---

### ⚙️ Backend API (FastAPI)
**API REST:**
```
https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai
```

**Endpoints Disponibili:**
- `GET /health` - Health check
- `GET /api/crm/orders` - Import ordini CRM
- `POST /api/optimize` - Ottimizzazione percorsi
- `GET /api/config/strategies` - Strategie OR-Tools

**Documentazione Swagger UI:**
```
https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/docs
```
👉 **API Docs interattiva:** https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/docs

---

## 🎯 Come Utilizzare l'Applicazione

### Step 1: Apri l'Applicazione
Clicca sul link frontend:
👉 https://3001-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai

### Step 2: Configura la Flotta
**Colonna Sinistra:**
- Numero Veicoli: `3`
- Capacità Veicolo: `100` kg
- Latitudine Deposito: `41.9028`
- Longitudine Deposito: `12.4964`

**Colonna Destra:**
- Time Limit: `30` secondi
- First Solution Strategy: `PATH_CHEAPEST_ARC`
- Local Search: `GUIDED_LOCAL_SEARCH`

### Step 3: Importa Ordini
Clicca il bottone **"📥 Importa da CRM"**
- Verranno caricati 20 ordini simulati
- Coordinate reali nell'area di Roma
- Visualizzati in tabella e sulla mappa

### Step 4: Ottimizza
Clicca il bottone **"🚀 Ottimizza Percorsi"**
- L'algoritmo OR-Tools calcola i percorsi ottimali
- Tempo di elaborazione: 2-5 secondi

### Step 5: Visualizza Risultati
- **Mappa**: Percorsi colorati per ogni veicolo
- **Statistiche**: Distanza totale, carico, veicoli usati
- **Dettagli**: Click sui veicoli per vedere le fermate

---

## 🧪 Test Rapidi

### Test Backend (via curl)

#### 1. Health Check
```bash
curl https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/health
```
**Output Atteso:**
```json
{"status":"healthy","service":"routing-optimizer"}
```

#### 2. Import Ordini
```bash
curl "https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/api/crm/orders?num_orders=5"
```
**Output Atteso:** JSON con 5 ordini simulati

#### 3. Strategie Disponibili
```bash
curl https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/api/config/strategies
```
**Output Atteso:** Liste strategie e metaheuristics

---

## 🔧 Configurazione Tecnica

### Frontend (Vite + React)
- **Porta**: 3001
- **Host**: 0.0.0.0
- **Allowed Hosts**: `.sandbox.novita.ai`, `localhost`
- **Proxy API**: `/api` → `http://localhost:8000`

### Backend (FastAPI + OR-Tools)
- **Porta**: 8000
- **Host**: 0.0.0.0
- **CORS**: Abilitato per tutti gli origin
- **Timeout**: 120 secondi

---

## 📚 Documentazione Completa

### File Disponibili
1. **README.md** - Guida completa utente/sviluppatore
2. **ARCHITECTURE.md** - Architettura tecnica dettagliata
3. **PROJECT_SUMMARY.md** - Riepilogo completo progetto
4. **DEPLOYMENT_INFO.md** - Info deployment e testing
5. **QUICK_START.md** - Guida rapida 5 minuti
6. **CONSEGNA_PROGETTO.md** - Checklist consegna
7. **ACCESS_INFO.md** - Questo file

### Posizione
Tutti i file sono nella directory principale del progetto:
```
/home/user/webapp/routing-optimizer/
```

---

## 🐛 Troubleshooting

### Problema: "Host not allowed"
**Soluzione:** ✅ RISOLTO
- Aggiornato `vite.config.ts` con `allowedHosts`
- Riavviato server Vite
- Nuovo URL sulla porta 3001

### Problema: Frontend non si connette al backend
**Soluzione:**
- Verifica che il backend sia attivo su porta 8000
- Le chiamate API usano il proxy `/api`
- Controlla la console del browser per errori

### Problema: Ottimizzazione fallisce
**Causa:** Capacità totale insufficiente
**Soluzione:**
- Aumenta numero veicoli o capacità
- Riduci numero ordini per test
- Aumenta time limit

---

## 📊 Performance & Limiti

### Performance Tipiche
- **5 ordini, 2 veicoli**: ~0.5 secondi
- **20 ordini, 3 veicoli**: ~2-5 secondi
- **50 ordini, 5 veicoli**: ~10-30 secondi

### Limiti Consigliati
- **Max Ordini**: 100 (ottimale: 20-50)
- **Max Veicoli**: 50 (ottimale: 3-10)
- **Max Time Limit**: 300s (5 minuti)

---

## 🎨 Screenshot Workflow

### 1. Pagina Iniziale
- Welcome message con istruzioni
- Form configurazione a 2 colonne
- Bottoni azione

### 2. Dopo Import CRM
- Tabella 20 ordini popolata
- Marker blu sulla mappa
- Statistiche peso totale

### 3. Dopo Ottimizzazione
- Polilinee colorate per veicolo
- Marker verdi per clienti assegnati
- Dashboard con statistiche
- Lista veicoli espandibile

---

## 💡 Tips per Risultati Migliori

### Configurazione Ottimale
1. **Bilanciamento**: Numero veicoli × capacità ≥ domanda totale
2. **Time Limit**: 30-60 secondi per 20 ordini
3. **Strategia**: PATH_CHEAPEST_ARC (veloce e buona)
4. **Metaheuristic**: GUIDED_LOCAL_SEARCH (bilanciata)

### Per Test Rapidi
- Riduci ordini a 5-10
- Time limit 10-15 secondi
- 2 veicoli con capacità alta

### Per Risultati Ottimali
- Usa tutti i 20 ordini
- Time limit 60+ secondi
- 3-5 veicoli bilanciati
- Prova diverse strategie

---

## 🔗 Link Utili

### Applicazione
- **Frontend**: https://3001-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai
- **Backend**: https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai
- **API Docs**: https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/docs

### Documentazione Esterna
- [Google OR-Tools](https://developers.google.com/optimization)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Leaflet](https://leafletjs.com/)
- [Tailwind CSS](https://tailwindcss.com/)

---

## ✅ Checklist Pre-Utilizzo

Prima di iniziare, verifica:
- [x] ✅ Backend attivo (porta 8000)
- [x] ✅ Frontend attivo (porta 3001)
- [x] ✅ Host allowed configurato
- [x] ✅ URL pubblici accessibili
- [x] ✅ Documentazione disponibile

---

## 🎉 Pronto all'Uso!

L'applicazione è **completamente funzionante** e pronta per:
- ✅ Demo immediate
- ✅ Testing e sperimentazione
- ✅ Valutazione algoritmi
- ✅ Presentazioni
- ✅ Estensioni future

---

## 📞 Quick Access

### 🖥️ Applicazione Web
👉 **ACCEDI ORA:** https://3001-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai

### 📖 API Documentation
👉 **ESPLORA API:** https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/docs

---

**Buona ottimizzazione! 🚚📦**

*Last updated: 2025-12-17*  
*Version: 1.0.1 (Fixed host issue)*  
*Status: 🟢 Fully Operational*
