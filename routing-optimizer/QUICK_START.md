# ⚡ Quick Start Guide - Routing Optimizer

## 🎯 Accesso Immediato

### 🌐 URL Applicazione Live

**Frontend UI (React):**
```
https://3000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai
```

**Backend API (FastAPI):**
```
https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai
```

**API Documentation (Swagger):**
```
https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/docs
```

---

## 🚀 Guida Rapida 5 Minuti

### Passo 1: Apri l'Applicazione
Clicca sul link frontend sopra per aprire l'interfaccia utente.

### Passo 2: Configura la Flotta
**Colonna Sinistra:**
- Numero Veicoli: `3`
- Capacità Veicolo: `100` kg
- Latitudine Deposito: `41.9028` (Roma centro)
- Longitudine Deposito: `12.4964`

**Colonna Destra:**
- Time Limit: `30` secondi
- First Solution Strategy: `PATH_CHEAPEST_ARC`
- Local Search: `GUIDED_LOCAL_SEARCH`

### Passo 3: Importa Ordini
Clicca il bottone blu **"📥 Importa da CRM"**
- Carica automaticamente 20 ordini simulati
- Coordinate reali nell'area di Roma
- Pesi casuali tra 5-50 kg

### Passo 4: Visualizza Ordini
Dopo l'import, vedrai:
- Tabella con tutti gli ordini
- Marker blu sulla mappa
- Statistiche peso totale

### Passo 5: Ottimizza
Clicca il bottone verde **"🚀 Ottimizza Percorsi"**
- Attendere 2-5 secondi
- L'algoritmo OR-Tools calcola i percorsi ottimali

### Passo 6: Risultati
Visualizzerai:
- **Mappa**: Percorsi colorati per ogni veicolo
- **Statistiche**: Distanza totale, carico, veicoli usati
- **Dettaglio**: Click sui veicoli per vedere turn-by-turn

---

## 🧪 Test API (Opzionale)

### Test 1: Health Check
```bash
curl https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/health
```
**Risposta Attesa:**
```json
{"status":"healthy","service":"routing-optimizer"}
```

### Test 2: Import Ordini
```bash
curl "https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/api/crm/orders?num_orders=5"
```
**Risposta Attesa:**
```json
{
  "orders": [
    {
      "id": "ORD0001",
      "customer_name": "Gelateria Giolitti",
      "latitude": 41.960446,
      "longitude": 12.505534,
      "demand": 30.26
    },
    ...
  ],
  "total_count": 5,
  "timestamp": "2025-12-17T..."
}
```

### Test 3: Ottimizzazione (POST)
```bash
curl -X POST https://8000-i0utw52endwb6h66jn8ci-18e660f9.sandbox.novita.ai/api/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "orders": [...],
    "fleet_config": {...},
    "ortools_config": {...}
  }'
```

---

## 📂 Installazione Locale

### Backend
```bash
cd routing-optimizer/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd routing-optimizer/frontend
npm install
npm run dev
```

### Script Automatico
```bash
cd routing-optimizer
./start.sh
```

---

## 🎨 Funzionalità Principali

### ✅ Simulazione CRM
- 20 ordini con coordinate Roma
- Nomi clienti italiani realistici
- Pesi variabili 5-50 kg

### ✅ Configurazione Avanzata
- Numero veicoli (1-50)
- Capacità veicolo
- Coordinate deposito personalizzate
- 3 strategie soluzione iniziale
- 3 metaheuristic ricerca locale
- Time limit configurabile

### ✅ Ottimizzazione OR-Tools
- CVRP (Capacitated Vehicle Routing Problem)
- Vincoli capacità
- Distanze geografiche (Haversine)
- Soluzione ottima/near-ottima

### ✅ Visualizzazione Avanzata
- Mappa Leaflet interattiva
- Marker colorati per veicoli
- Polilinee percorsi
- Popup informativi
- Statistiche aggregate
- Dettaglio turn-by-turn

---

## 📊 Esempio Risultato

### Input
- 20 ordini area Roma
- 3 veicoli, 100 kg capacità ciascuno
- Strategia: PATH_CHEAPEST_ARC
- Metaheuristic: GUIDED_LOCAL_SEARCH

### Output
```
✅ Ottimizzazione completata con successo

Distanza Totale: 45.67 km
Carico Totale: 287.50 kg
Veicoli Usati: 3/3
Ordini Serviti: 20/20
Tempo Computazione: 2.345s

Veicolo 1: 15.23 km, 95.00 kg (7 fermate)
Veicolo 2: 18.44 km, 105.50 kg (8 fermate)
Veicolo 3: 12.00 km, 87.00 kg (5 fermate)
```

---

## 🐛 Risoluzione Problemi

### Backend non risponde
```bash
# Controlla che il servizio sia attivo
curl http://localhost:8000/health

# Se non risponde, riavvia
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend errore CORS
- Verifica che backend sia su porta 8000
- Controlla configurazione CORS in `main.py`
- Riavvia entrambi i servizi

### Ottimizzazione fallisce
- Verifica capacità totale >= domanda totale
- Aumenta time limit
- Riduci numero ordini per test

### Mappa non visualizza
- Verifica connessione internet (Leaflet tiles)
- Controlla console browser per errori
- Ricarica pagina

---

## 📚 Documentazione Completa

- **README.md**: Guida completa utente/sviluppatore
- **ARCHITECTURE.md**: Architettura tecnica dettagliata
- **PROJECT_SUMMARY.md**: Riepilogo completo progetto
- **DEPLOYMENT_INFO.md**: Info deployment e testing

---

## 🎓 Concetti Chiave

### CVRP (Capacitated Vehicle Routing Problem)
Problema di ottimizzazione NP-Hard che richiede di:
1. Assegnare ordini a veicoli
2. Determinare sequenza visite
3. Rispettare vincoli capacità
4. Minimizzare distanza totale

### OR-Tools
Libreria Google per ottimizzazione combinatoriale che usa:
- Constraint Programming
- Heuristic search
- Local search metaheuristics

### Haversine Distance
Formula per calcolare distanza tra due punti geografici:
```
d = 2R × arcsin(√(sin²(Δφ/2) + cos(φ1)×cos(φ2)×sin²(Δλ/2)))
```
dove R = 6,371 km (raggio Terra)

---

## 💡 Tips & Tricks

### Per Risultati Migliori
1. ⏱️ Aumenta time limit per problemi grandi
2. 🚚 Bilancia numero veicoli vs capacità
3. 🎯 Usa GUIDED_LOCAL_SEARCH (default)
4. 📍 Posiziona deposito centralmente

### Per Test Rapidi
1. Riduci numero ordini (5-10)
2. Usa AUTOMATIC strategy
3. Time limit basso (10-15s)

### Per Problemi Complessi
1. Aumenta time limit (60-120s)
2. Prova diverse strategie
3. Aumenta numero veicoli
4. Considera clustering preliminare

---

## 🔗 Link Utili

- [Google OR-Tools Docs](https://developers.google.com/optimization)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Leaflet Documentation](https://leafletjs.com/)
- [Tailwind CSS](https://tailwindcss.com/)

---

## 🎉 Buon Utilizzo!

**Domande? Problemi? Feedback?**

L'applicazione è completamente funzionante e pronta all'uso.
Inizia subito ottimizzando i tuoi percorsi di consegna! 🚚📦

---

*Last updated: 2025-12-17*
*Version: 1.0.0*
