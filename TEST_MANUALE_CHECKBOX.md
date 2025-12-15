# 🧪 TEST MANUALE CHECKBOX - Copia e Incolla nella Console

## Step 1: Apri l'App Principale
```
https://8000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai
```

## Step 2: Vai in "Anagrafica Mezzi"

## Step 3: Apri Console Browser (F12)

## Step 4: Incolla questo codice nella Console e premi INVIO

```javascript
// === TEST MANUALE CHECKBOX ===
console.clear();
console.log('🧪 Starting manual checkbox test...');

// 1. Verifica mezziList esiste
const mezziList = document.getElementById('mezziList');
if (!mezziList) {
    console.error('❌ FATAL: mezziList element NOT FOUND!');
} else {
    console.log('✅ mezziList element found:', mezziList);
}

// 2. Verifica vehicles array
if (typeof vehicles === 'undefined') {
    console.error('❌ FATAL: vehicles array NOT DEFINED!');
} else {
    console.log('✅ vehicles array exists:', vehicles.length, 'vehicles');
    console.log('   First vehicle:', vehicles[0]);
}

// 3. Verifica checkboxes esistono
const checkboxes = document.querySelectorAll('#mezziList input[type="checkbox"][data-action="toggle-availability"]');
console.log('📊 Found', checkboxes.length, 'checkboxes');

if (checkboxes.length === 0) {
    console.error('❌ NO CHECKBOXES FOUND!');
    console.log('💡 Try: renderVehiclesList() to render vehicles');
} else {
    const firstCheckbox = checkboxes[0];
    console.log('✅ First checkbox:', firstCheckbox);
    console.log('   data-id:', firstCheckbox.dataset.id);
    console.log('   data-action:', firstCheckbox.dataset.action);
    console.log('   checked:', firstCheckbox.checked);
}

// 4. Test event listener manualmente
console.log('\n🔧 MANUAL TEST: Simulating checkbox click...');
if (vehicles && vehicles.length > 0 && checkboxes.length > 0) {
    const firstVehicle = vehicles[0];
    const oldState = firstVehicle.isAvailable;
    
    console.log('Before:', firstVehicle.targa, 'isAvailable =', oldState);
    
    // Toggle manualmente
    firstVehicle.isAvailable = !oldState;
    saveVehicles();
    
    console.log('After:', firstVehicle.targa, 'isAvailable =', firstVehicle.isAvailable);
    console.log('💾 Saved to localStorage');
    
    // Re-render
    renderVehiclesList();
    renderAvailableVehiclesList();
    
    console.log('🔄 Re-rendered');
    console.log('\n✅ MANUAL TEST COMPLETE');
    console.log('👀 Check if the background color changed!');
} else {
    console.error('❌ Cannot run manual test - missing data');
}

console.log('\n📋 NEXT STEPS:');
console.log('1. Check if background color changed after manual test');
console.log('2. Now try clicking a checkbox with your mouse');
console.log('3. Watch for console logs starting with 🎯');
```

## Step 5: Guarda l'Output

Dopo aver eseguito il codice, **copia TUTTO l'output della console** e inviamelo.

---

## Step 6: Clicca Fisicamente un Checkbox

Dopo il test manuale, **clicca con il mouse** su un checkbox e dimmi se appare:
```
🎯 CLICK event on mezziList: ...
```

---

## Risultati Attesi

### ✅ Se il test manuale funziona:
- Console mostra: `✅ MANUAL TEST COMPLETE`
- Lo sfondo della riga dovrebbe cambiare colore
- Questo significa: il codice funziona, ma l'event listener non è attaccato

### ❌ Se il test manuale NON funziona:
- Console mostra errori
- Lo sfondo NON cambia
- Questo significa: problema nel codice render o save

### 🎯 Se vedi "🎯 CLICK event" quando clicchi:
- L'event listener funziona!
- Seguire i log per vedere dove si blocca

### 😶 Se NON vedi nulla quando clicchi:
- L'event listener NON è attaccato
- Problema nell'inizializzazione

---

## Inviami:
1. ✅ Output completo del test manuale (Step 4)
2. ✅ Cosa succede quando clicchi fisicamente il checkbox (Step 6)
3. ✅ Screenshot se possibile

Con queste informazioni posso risolvere definitivamente! 🎯
