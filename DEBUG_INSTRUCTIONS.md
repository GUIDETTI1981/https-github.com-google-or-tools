# 🔍 ISTRUZIONI DEBUG - Checkbox Attivo Non Funziona

## 📋 Problema
Il checkbox "Attivo" in Anagrafica Mezzi non risponde ai click.

---

## 🧪 Test Step-by-Step

### TEST 1: Pagina Semplificata (Verifica Codice Base)

1. **Apri la pagina di test**:
   ```
   https://8000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/test_checkbox_simple.html
   ```

2. **Apri Console Browser** (F12 → Tab "Console")

3. **Clicca sui checkbox** nella pagina di test

4. **Verifica risultati**:
   - ✅ **Se funziona**: Il problema è nell'integrazione con l'app principale
   - ❌ **Se NON funziona**: Problema nel browser o configurazione

---

### TEST 2: Applicazione Principale con Debug

1. **Apri l'app principale**:
   ```
   https://8000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/index.html
   ```

2. **Apri Console Browser** (F12 → Tab "Console")

3. **Vai nel tab "Anagrafica Mezzi"**

4. **Verifica cosa appare in Console**:
   ```
   🔄 renderVehiclesList called, vehicles count: X
     - Rendering vehicle: [TARGA], isAvailable: [true/false], id: [ID]
   ```
   
   **Se NON appare**:
   - ❌ `renderVehiclesList()` non viene chiamato
   - Possibile causa: tab non si apre correttamente
   
   **Se appare**:
   - ✅ Veicoli caricati correttamente
   - Procedi al prossimo test

5. **Clicca su un checkbox "Attivo"**

6. **Verifica log in Console**:
   ```
   Change event triggered on: <input type="checkbox" ...>
   Target type: checkbox
   Target action: toggle-availability
   Vehicle ID: [ID]
   All vehicles: [Array]
   Found vehicle: {id: ..., targa: ..., ...}
   Setting isAvailable to true for [TARGA]
   ✅ Mezzo [TARGA] attivato
   ```

---

## 🔍 Analisi Log Console

### Scenario A: NESSUN LOG appare quando clicchi checkbox
**Diagnosi**: Event listener non attaccato o checkbox non trovato

**Verifica manualmente in Console**:
```javascript
// Verifica elemento mezziList esiste
document.getElementById('mezziList')

// Verifica checkbox esistono
document.querySelectorAll('input[type="checkbox"][data-action="toggle-availability"]')

// Forza attaccamento event listener manualmente
const mezziList = document.getElementById('mezziList');
mezziList.addEventListener('change', (e) => {
    console.log('MANUAL EVENT LISTENER:', e.target);
});
```

---

### Scenario B: Log appare ma dice "Not a toggle-availability checkbox"
**Diagnosi**: Attributo `data-action` non impostato correttamente

**Verifica manualmente in Console**:
```javascript
// Ispeziona primo checkbox
const checkbox = document.querySelector('input[type="checkbox"]');
console.log('Checkbox:', checkbox);
console.log('data-action:', checkbox.dataset.action);
console.log('data-id:', checkbox.dataset.id);
```

---

### Scenario C: Log appare ma dice "❌ Vehicle not found!"
**Diagnosi**: Mismatch tra ID nel checkbox e ID nell'array vehicles

**Verifica manualmente in Console**:
```javascript
// Mostra tutti gli ID dei veicoli
vehicles.map(v => ({ id: v.id, targa: v.targa }))

// Mostra tutti gli ID nei checkbox
Array.from(document.querySelectorAll('input[data-action="toggle-availability"]'))
    .map(input => ({ id: input.dataset.id }))

// Verifica tipo
const checkbox = document.querySelector('input[data-action="toggle-availability"]');
console.log('Checkbox ID type:', typeof checkbox.dataset.id);
console.log('Vehicle ID type:', typeof vehicles[0].id);
```

**Se i tipi sono diversi (string vs number)**:
```javascript
// Fix temporaneo: converti ID
const vehicleId = String(checkbox.dataset.id); // o Number()
```

---

### Scenario D: Log appare, vehicle trovato, ma UI non si aggiorna
**Diagnosi**: `renderVehiclesList()` non funziona correttamente

**Verifica manualmente in Console**:
```javascript
// Forza re-render
renderVehiclesList()

// Verifica se vehicles è aggiornato
vehicles.filter(v => v.isAvailable)

// Verifica localStorage
JSON.parse(localStorage.getItem('vehiclesData'))
```

---

## 🛠️ Fix Manuali in Console

### Fix 1: Attivare manualmente un mezzo
```javascript
// Trova mezzo per targa
const mezzo = vehicles.find(v => v.targa === 'AA123BB'); // Sostituisci con targa reale

// Attiva
mezzo.isAvailable = true;

// Salva
localStorage.setItem('vehiclesData', JSON.stringify(vehicles));

// Re-render
renderVehiclesList();
renderAvailableVehiclesList();
```

### Fix 2: Attivare TUTTI i mezzi
```javascript
// Attiva tutti
vehicles.forEach(v => v.isAvailable = true);

// Salva
localStorage.setItem('vehiclesData', JSON.stringify(vehicles));

// Re-render
renderVehiclesList();
renderAvailableVehiclesList();
```

### Fix 3: Reset completo localStorage
```javascript
// ATTENZIONE: Cancella TUTTI i dati!
localStorage.clear();

// Ricarica pagina
location.reload();
```

---

## 📊 Checklist Debug

### Verifica 1: Elemento DOM
- [ ] `document.getElementById('mezziList')` ritorna un elemento (non null)
- [ ] L'elemento è visibile nella pagina
- [ ] L'elemento è nel tab "Anagrafica Mezzi"

### Verifica 2: Dati Veicoli
- [ ] `vehicles` è definito (non undefined)
- [ ] `vehicles.length > 0` (ci sono veicoli)
- [ ] Ogni veicolo ha proprietà `id`, `targa`, `isAvailable`

### Verifica 3: Rendering
- [ ] `renderVehiclesList()` viene chiamato
- [ ] Checkbox appaiono nella tabella
- [ ] Checkbox hanno attributi `data-id` e `data-action`

### Verifica 4: Event Listener
- [ ] Cliccando checkbox appare log in Console
- [ ] Log mostra "Change event triggered"
- [ ] Log mostra vehicle ID corretto
- [ ] Log mostra "Found vehicle" con dati corretti

### Verifica 5: Aggiornamento Stato
- [ ] `vehicle.isAvailable` cambia valore
- [ ] `saveVehicles()` viene chiamato
- [ ] `renderVehiclesList()` viene chiamato dopo cambio
- [ ] UI si aggiorna (sfondo verde/grigio)

---

## 🎯 Risultati Attesi

### ✅ Funzionamento Corretto
1. Click checkbox → log "Change event triggered"
2. Log "Found vehicle: ..."
3. Log "✅ Mezzo [TARGA] attivato"
4. Sfondo riga diventa verde
5. Testo "Sì" in verde appare
6. Vai in "Pianificazione" → mezzo appare automaticamente

### ❌ Problema Identificato
Se uno degli step sopra fallisce, il problema è in quello step.

---

## 📝 Copia questi comandi nella Console e inviami i risultati

```javascript
// === DIAGNOSTIC REPORT ===
console.log('=== VEHICLE DIAGNOSTIC REPORT ===');

// 1. Check mezziList exists
console.log('1. mezziList element:', document.getElementById('mezziList') ? 'EXISTS' : 'NOT FOUND');

// 2. Check vehicles array
console.log('2. vehicles array:', vehicles ? `EXISTS (${vehicles.length} vehicles)` : 'NOT DEFINED');

// 3. Check checkboxes
const checkboxes = document.querySelectorAll('input[type="checkbox"][data-action="toggle-availability"]');
console.log('3. Checkboxes found:', checkboxes.length);

// 4. Check first checkbox attributes
if (checkboxes.length > 0) {
    const firstCheckbox = checkboxes[0];
    console.log('4. First checkbox data-id:', firstCheckbox.dataset.id);
    console.log('   First checkbox data-action:', firstCheckbox.dataset.action);
    console.log('   First checkbox checked:', firstCheckbox.checked);
}

// 5. Check vehicles IDs
if (vehicles && vehicles.length > 0) {
    console.log('5. Vehicle IDs:', vehicles.map(v => v.id));
    console.log('   Vehicle IDs types:', vehicles.map(v => typeof v.id));
}

// 6. Check localStorage
const storedVehicles = localStorage.getItem('vehiclesData');
console.log('6. localStorage has vehiclesData:', storedVehicles ? 'YES' : 'NO');

console.log('=== END DIAGNOSTIC REPORT ===');
```

---

## 📱 Link Test

- **App Principale**: https://8000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/index.html
- **Test Semplificato**: https://8000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai/test_checkbox_simple.html

---

**Dopo aver eseguito i test, inviami**:
1. Screenshot o copia della Console
2. Quale scenario si verifica (A, B, C, o D)
3. Output del "DIAGNOSTIC REPORT"

Con queste informazioni potrò identificare esattamente il problema! 🔍
