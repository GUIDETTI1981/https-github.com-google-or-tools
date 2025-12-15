# Sistema di Gestione Ritiri con OR-Tools

Sistema di pianificazione logistica ottimizzato con Google OR-Tools per la gestione dei ritiri di ceramiche.

## 🚀 Caratteristiche Principali

### ✅ Ottimizzazione con OR-Tools
- **Vehicle Routing Problem (VRP)** con time windows e capacità
- **Vincoli di zona** con regole di compatibilità
- **Gestione priorità** (urgenze e prenotazioni)
- **Ottimizzazione multi-obiettivo**: minimizzazione km e tempi morti

### 🎯 Vincoli Implementati

1. **Capacità Mezzi**: Rispetto dei limiti di carico (kg)
2. **Time Windows**: Fasce orarie di carico per ceramiche/depositi
3. **Zone Geografiche**: 
   - Gruppo A: SOLIGNANO, UBERSETTO, FIORANO 1-2, SASSUOLO 1-2, ROTEGLIA
   - Gruppo B: SCANDIANO, CASALGRANDE, S.ANTONINO, ROTEGLIA
   - Gruppo C: RUBIERA, VILLALUNGA, ROTEGLIA
   - Esclusioni speciali per ceramiche specifiche
4. **Priorità**: Prenotazioni e urgenze hanno priorità assoluta
5. **Regole Mezzi Pesanti**: Camion >12t non vanno su carichi <2t (salvo urgenze)

## 📁 Struttura Progetto

```
webapp/
├── index.html          # Frontend applicazione
├── api.py              # API Flask per OR-Tools
├── optimizer.py        # Motore di ottimizzazione OR-Tools
├── requirements.txt    # Dipendenze Python
└── README.md          # Questo file
```

## 🛠️ Installazione

### Prerequisiti
- Python 3.8+
- pip

### Setup

1. **Installa dipendenze**:
```bash
cd /home/user/webapp
pip install -r requirements.txt
```

2. **Avvia API OR-Tools**:
```bash
python api.py
```
L'API sarà disponibile su `http://localhost:5000`

3. **Avvia Frontend** (in un'altra shell):
```bash
python -m http.server 8000
```
Il frontend sarà disponibile su `http://localhost:8000`

## 🌐 URL Pubblici (Sandbox)

- **Frontend**: https://8000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai
- **API OR-Tools**: https://5000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai
- **Health Check API**: https://5000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/health

## 📖 Utilizzo

### 1. Anagrafica
- **Ceramiche**: Aggiungi ceramiche con regole di carico (orari, tempi medi)
- **Clienti**: Gestisci clienti destinatari
- **Depositi**: Configura depositi alternativi
- **Mezzi**: Aggiungi mezzi con portata e autista

### 2. Pianificazione Ritiri

1. Vai alla tab **"Regole di Ingaggio"**
2. Clicca **"Importa Ordini"** e seleziona la data
3. Seleziona le **fasce orarie** (Mattino/Pomeriggio)
4. Seleziona i **mezzi disponibili** per ciascuna fascia
5. Clicca **"AVVIA OTTIMIZZAZIONE"**

### 3. Risultati

Nella tab **"Risultati Ottimizzazione"** troverai:
- **Giri del Mattino**: Route ottimizzate per la fascia 06:00-12:00
- **Giri del Pomeriggio**: Route ottimizzate per la fascia 14:00-18:00
- **Non Assegnati**: Fermate che non rispettano i vincoli

Puoi:
- 🗺️ **Visualizzare mappa** del percorso
- 📋 **Vedere dettagli** dei ritiri (doppio click)
- 🔀 **Modificare manualmente** con drag & drop

## 🔧 API Endpoints

### Health Check
```bash
GET /health
```
Verifica stato del servizio

### Ottimizzazione
```bash
POST /api/optimize
Content-Type: application/json

{
  "stops": [...],
  "morningVehicles": [...],
  "afternoonVehicles": [...],
  "timeWindows": ["mattino", "pomeriggio"]
}
```

### Test
```bash
POST /api/test
```
Esegue ottimizzazione con dati di esempio

## 🧪 Test API

```bash
# Health check
curl https://5000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/health

# Test ottimizzazione
curl -X POST https://5000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/api/test
```

## 🏗️ Architettura Tecnica

### Backend (Python)
- **OR-Tools 9.14**: Solver per VRP con constraint programming
- **Flask 3.1**: API REST
- **NumPy**: Calcoli matrici distanze/tempi

### Frontend (JavaScript)
- **Vanilla JS**: Nessun framework pesante
- **Leaflet**: Mappe interattive
- **Tailwind CSS**: Styling
- **LocalStorage**: Persistenza dati client-side

### Algoritmo OR-Tools

1. **Modellazione**:
   - Depot (hub) come nodo 0
   - Stops come nodi 1..N
   - Matrice distanze euclidee approssimate

2. **Dimensioni**:
   - **Capacity**: Vincolo portata mezzi
   - **Time**: Time windows per ciascun nodo

3. **Strategia di ricerca**:
   - First solution: PATH_CHEAPEST_ARC
   - Local search: GUIDED_LOCAL_SEARCH
   - Timeout: 30 secondi

4. **Penalità**:
   - Nodi non visitati: 100,000
   - Permette soluzioni parziali

## 📊 Metriche di Ottimizzazione

L'algoritmo ottimizza per:
- ✅ Minimizzazione distanza totale percorsa
- ✅ Rispetto time windows
- ✅ Saturazione capacità mezzi
- ✅ Compatibilità zone geografiche
- ✅ Priorità urgenze/prenotazioni

## 🐛 Troubleshooting

### L'ottimizzazione non parte
- Verifica che l'API sia attiva: `curl http://localhost:5000/health`
- Controlla che ci siano ordini importati
- Assicurati di aver selezionato almeno una fascia oraria
- Verifica che ci siano mezzi disponibili per la fascia selezionata

### Molti ritiri "Non Assegnati"
- Aumenta il numero di mezzi disponibili
- Verifica la capacità dei mezzi (kg)
- Controlla le regole di zona delle ceramiche
- Rivedi le time windows

### Errori CORS
- L'API Flask ha CORS abilitato
- Se usi un dominio diverso, aggiorna l'URL nell'index.html

## 📝 Note di Sviluppo

### Coordinare geografiche
Le ceramiche devono avere coordinate GPS per l'ottimizzazione. Se mancanti:
- Usa il pulsante **"Su Mappa"** per posizionare manualmente
- Oppure compila indirizzo completo per geocoding automatico

### Persistenza dati
- I dati sono salvati nel localStorage del browser
- Esporta/importa per backup o migrazione

### Performance
- OR-Tools può richiedere 10-30 secondi per problemi complessi (>30 stops)
- Il timeout è configurabile in `optimizer.py` (parametro `time_limit`)

## 🔮 Sviluppi Futuri

- [ ] Integrazione con sistema gestionale (ERP)
- [ ] Geocoding real-time con API Google Maps
- [ ] Calcolo distanze reali (non euclidee)
- [ ] Multi-depot support
- [ ] Esportazione PDF dei giri
- [ ] Notifiche SMS/Email agli autisti
- [ ] Dashboard statistiche storiche

## 👥 Supporto

Per problemi o domande:
1. Verifica i log della console del browser (F12)
2. Controlla i log del server Flask
3. Consulta la documentazione OR-Tools: https://developers.google.com/optimization

## 📄 Licenza

Uso interno aziendale

---

**Powered by Google OR-Tools** 🚀
