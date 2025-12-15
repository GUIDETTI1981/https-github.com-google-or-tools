# 📥 Guida Installazione Locale

## 🎯 Scarica la Web App

### **Metodo 1: Download Diretto** ⭐ (Consigliato)

**Scarica l'archivio completo:**
```
https://8000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/webapp_ortools_ritiri.tar.gz
```

Dimensione: **~57KB** (compresso)

---

### **Metodo 2: Download File Singoli**

Scarica manualmente dal server:

**URL Base:** `https://8000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/`

**File Principali:**
- `index.html` - Frontend applicazione (132KB)
- `api.py` - Backend API Flask (6KB)
- `optimizer.py` - Motore OR-Tools (18KB)
- `requirements.txt` - Dipendenze Python
- `README.md` - Documentazione
- `start_services.sh` - Script avvio
- `test_integration.py` - Test

---

### **Metodo 3: Git Clone (Se configurato)**

```bash
git clone <repository_url>
cd webapp
```

---

## 🛠️ Installazione su Computer Locale

### **Prerequisiti**

- Python 3.8 o superiore
- pip (gestore pacchetti Python)
- Connessione internet (per installare dipendenze)

### **Windows**

```cmd
REM 1. Estrai l'archivio
tar -xzf webapp_ortools_ritiri.tar.gz
cd webapp

REM 2. Crea ambiente virtuale (opzionale ma consigliato)
python -m venv venv
venv\Scripts\activate

REM 3. Installa dipendenze
pip install -r requirements.txt

REM 4. Avvia i servizi
REM Apri due terminali separati:

REM Terminal 1 - API Backend
python api.py

REM Terminal 2 - Frontend
python -m http.server 8000
```

### **macOS / Linux**

```bash
# 1. Estrai l'archivio
tar -xzf webapp_ortools_ritiri.tar.gz
cd webapp

# 2. Crea ambiente virtuale (opzionale ma consigliato)
python3 -m venv venv
source venv/bin/activate

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Rendi eseguibile lo script di avvio
chmod +x start_services.sh

# 5. Avvia tutto automaticamente
./start_services.sh
```

**Oppure manualmente:**
```bash
# Terminal 1 - API Backend
python api.py

# Terminal 2 - Frontend
python -m http.server 8000
```

---

## 🌐 Accesso Applicazione Locale

Dopo aver avviato i servizi, apri il browser e vai a:

```
http://localhost:8000
```

**API Backend:**
```
http://localhost:5000
http://localhost:5000/health
```

---

## ⚙️ Configurazione URL API

Se l'API Backend è su un host diverso, modifica `index.html`:

Cerca questa riga (~1800):
```javascript
const response = await fetch('https://5000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/api/optimize', {
```

Sostituisci con:
```javascript
const response = await fetch('http://localhost:5000/api/optimize', {
```

**Oppure usa questo comando:**
```bash
# Linux/macOS
sed -i 's|https://5000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai|http://localhost:5000|g' index.html

# Windows (PowerShell)
(Get-Content index.html) -replace 'https://5000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai', 'http://localhost:5000' | Set-Content index.html
```

---

## 🐳 Installazione con Docker (Opzionale)

Crea `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000 8000

CMD ["sh", "-c", "python api.py & python -m http.server 8000"]
```

**Build e Run:**
```bash
docker build -t ritiri-ortools .
docker run -p 5000:5000 -p 8000:8000 ritiri-ortools
```

---

## 🧪 Verifica Installazione

```bash
# Test API
curl http://localhost:5000/health

# Test completo
python test_integration.py
```

**Output atteso:**
```
✅ Health check OK
✅ Ottimizzazione completata!
🎉 Tutti i test sono passati!
```

---

## 🔧 Troubleshooting

### Errore: "ModuleNotFoundError: No module named 'ortools'"
```bash
pip install -r requirements.txt
```

### Errore: "Address already in use" (porta occupata)
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:5000 | xargs kill -9
```

### CORS Errors nel browser
- Verifica che l'API sia avviata su `http://localhost:5000`
- Controlla che Flask CORS sia abilitato (già configurato)

### Dipendenze non si installano
```bash
# Aggiorna pip
pip install --upgrade pip

# Installa con verbose
pip install -r requirements.txt -v
```

---

## 📦 Struttura Directory Locale

```
webapp/
├── index.html                    # Frontend applicazione
├── api.py                        # Backend Flask
├── optimizer.py                  # Motore OR-Tools
├── requirements.txt              # Dipendenze Python
├── start_services.sh             # Script avvio (Linux/macOS)
├── test_integration.py           # Test automatizzati
├── README.md                     # Documentazione completa
├── DEPLOYMENT_SUMMARY.md         # Riepilogo deployment
└── INSTALLAZIONE_LOCALE.md       # Questa guida
```

---

## 🚀 Avvio Rapido (Riepilogo)

### **1 Minuto Setup:**

```bash
# 1. Scarica ed estrai
curl -O https://8000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/webapp_ortools_ritiri.tar.gz
tar -xzf webapp_ortools_ritiri.tar.gz
cd webapp

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Avvia (Linux/macOS)
./start_services.sh

# 3. Avvia (Windows)
# Terminal 1: python api.py
# Terminal 2: python -m http.server 8000

# 4. Apri browser
# http://localhost:8000
```

---

## 📱 Deploy su Server Pubblico

### **Con Nginx + Gunicorn (Produzione)**

```bash
# Installa Gunicorn
pip install gunicorn

# Avvia API con Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app

# Configura Nginx
# /etc/nginx/sites-available/ritiri
server {
    listen 80;
    server_name tuodominio.com;
    
    location / {
        root /path/to/webapp;
        index index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔒 Note di Sicurezza

**Per uso in produzione:**

1. **Disabilita debug mode** in `api.py`:
   ```python
   app.run(host='0.0.0.0', port=5000, debug=False)
   ```

2. **Usa HTTPS** con certificato SSL

3. **Configura firewall** per limitare accessi

4. **Usa variabili d'ambiente** per configurazioni sensibili

5. **Implementa autenticazione** se necessario

---

## ℹ️ Informazioni Utili

- **Dimensione totale**: ~180KB (non compressa)
- **Dipendenze Python**: ~30MB (OR-Tools + Flask)
- **Requisiti RAM**: minimo 512MB
- **Requisiti CPU**: 1 core (2+ consigliati per ottimizzazioni complesse)

---

## 📞 Supporto

**Problemi comuni risolti in:**
- README.md
- DEPLOYMENT_SUMMARY.md

**Logs utili:**
```bash
# API logs
tail -f /tmp/ortools_api.log

# Console browser (F12)
```

---

## ✅ Checklist Post-Installazione

- [ ] Python 3.8+ installato
- [ ] Dipendenze installate (`pip list | grep ortools`)
- [ ] API Backend avviata (porta 5000)
- [ ] Frontend avviato (porta 8000)
- [ ] Health check OK (`curl http://localhost:5000/health`)
- [ ] Test passati (`python test_integration.py`)
- [ ] Browser aperto su `http://localhost:8000`
- [ ] URL API configurato correttamente in index.html

---

🎉 **Installazione completata! Buon utilizzo!**
