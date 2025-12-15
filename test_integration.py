"""
Script di test per l'integrazione OR-Tools
"""

import requests
import json
import sys

API_URL = "https://5000-i1d1tb5i6gnzkgewpmnk0-8f57ffe2.sandbox.novita.ai"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Test 1: Health Check...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check OK: {data}")
            return True
        else:
            print(f"❌ Health check fallito: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return False


def test_optimization_with_sample_data():
    """Test ottimizzazione con dati di esempio"""
    print("\n🔍 Test 2: Ottimizzazione con dati campione...")
    
    sample_data = {
        "stops": [
            {
                "key": "Ceramica Test A",
                "name": "Ceramica Test A",
                "coords": [44.55, 10.78],
                "totalWeight": 1500,
                "orders": [
                    {"id": "1", "cliente": "Cliente 1", "peso": 800, "ceramica": "Ceramica Test A"},
                    {"id": "2", "cliente": "Cliente 2", "peso": 700, "ceramica": "Ceramica Test A"}
                ],
                "loadingTime": 20,
                "zone": "FIORANO 1",
                "priorityScore": 0,
                "readyTime": "mattino",
                "appointment": None,
                "appointmentTime": None,
                "openingWindows": [{"start": 480, "end": 720}],
                "ceramicsDetail": {}
            },
            {
                "key": "Ceramica Test B",
                "name": "Ceramica Test B",
                "coords": [44.52, 10.75],
                "totalWeight": 2200,
                "orders": [
                    {"id": "3", "cliente": "Cliente 3", "peso": 1200, "ceramica": "Ceramica Test B"},
                    {"id": "4", "cliente": "Cliente 4", "peso": 1000, "ceramica": "Ceramica Test B"}
                ],
                "loadingTime": 25,
                "zone": "SASSUOLO 1",
                "priorityScore": 2,  # Urgente
                "readyTime": "mattino",
                "appointment": "2024-01-15",
                "appointmentTime": "10:00",
                "openingWindows": [{"start": 480, "end": 720}],
                "ceramicsDetail": {}
            },
            {
                "key": "Ceramica Test C",
                "name": "Ceramica Test C",
                "coords": [44.50, 10.80],
                "totalWeight": 1800,
                "orders": [
                    {"id": "5", "cliente": "Cliente 5", "peso": 1800, "ceramica": "Ceramica Test C"}
                ],
                "loadingTime": 22,
                "zone": "FIORANO 2",
                "priorityScore": 0,
                "readyTime": "pomeriggio",
                "appointment": None,
                "appointmentTime": None,
                "openingWindows": [{"start": 840, "end": 1080}],
                "ceramicsDetail": {}
            },
            {
                "key": "Ceramica Test D",
                "name": "Ceramica Test D",
                "coords": [44.53, 10.77],
                "totalWeight": 1600,
                "orders": [
                    {"id": "6", "cliente": "Cliente 6", "peso": 900, "ceramica": "Ceramica Test D"},
                    {"id": "7", "cliente": "Cliente 7", "peso": 700, "ceramica": "Ceramica Test D"}
                ],
                "loadingTime": 18,
                "zone": "SASSUOLO 2",
                "priorityScore": 0,
                "readyTime": "mattino",
                "appointment": None,
                "appointmentTime": None,
                "openingWindows": [{"start": 480, "end": 720}],
                "ceramicsDetail": {}
            }
        ],
        "morningVehicles": [
            {
                "id": "v1",
                "targa": "AB123CD",
                "autista": "Mario Rossi",
                "payload": 4000,
                "rules": {"maxStops": None, "mandatoryCeramics": []}
            },
            {
                "id": "v2",
                "targa": "EF456GH",
                "autista": "Luigi Verdi",
                "payload": 3500,
                "rules": {"maxStops": None, "mandatoryCeramics": []}
            }
        ],
        "afternoonVehicles": [
            {
                "id": "v3",
                "targa": "IJ789KL",
                "autista": "Paolo Bianchi",
                "payload": 4000,
                "rules": {"maxStops": None, "mandatoryCeramics": []}
            }
        ],
        "timeWindows": ["mattino", "pomeriggio"]
    }
    
    try:
        print(f"📤 Invio richiesta con {len(sample_data['stops'])} fermate...")
        response = requests.post(
            f"{API_URL}/api/optimize",
            json=sample_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                data = result['data']
                stats = result.get('stats', {})
                
                print("\n✅ Ottimizzazione completata!")
                print(f"📊 Statistiche:")
                print(f"   - Giri mattino: {len(data.get('morningRoutes', []))}")
                print(f"   - Giri pomeriggio: {len(data.get('afternoonRoutes', []))}")
                print(f"   - Fermate assegnate: {stats.get('totalAssigned', 0)}")
                print(f"   - Fermate non assegnate: {stats.get('totalUnassigned', 0)}")
                
                # Dettaglio giri mattino
                if data.get('morningRoutes'):
                    print("\n🌅 Giri del Mattino:")
                    for i, route in enumerate(data['morningRoutes'], 1):
                        vehicle = route['vehicle']
                        stops = route['stops']
                        total_weight = sum(s['totalWeight'] for s in stops)
                        print(f"   {i}. {vehicle['targa']} ({vehicle['autista']})")
                        print(f"      - {len(stops)} fermate, {total_weight} kg")
                        for j, stop in enumerate(stops, 1):
                            print(f"        {j}) {stop['name']} - {stop['totalWeight']}kg ({stop['zone']})")
                
                # Dettaglio giri pomeriggio
                if data.get('afternoonRoutes'):
                    print("\n🌆 Giri del Pomeriggio:")
                    for i, route in enumerate(data['afternoonRoutes'], 1):
                        vehicle = route['vehicle']
                        stops = route['stops']
                        total_weight = sum(s['totalWeight'] for s in stops)
                        print(f"   {i}. {vehicle['targa']} ({vehicle['autista']})")
                        print(f"      - {len(stops)} fermate, {total_weight} kg")
                        for j, stop in enumerate(stops, 1):
                            print(f"        {j}) {stop['name']} - {stop['totalWeight']}kg ({stop['zone']})")
                
                # Non assegnati
                if data.get('unassigned'):
                    print("\n⚠️  Fermate Non Assegnate:")
                    for stop in data['unassigned']:
                        print(f"   - {stop['name']}: {stop.get('reason', 'N/D')}")
                
                return True
            else:
                print(f"❌ Ottimizzazione fallita: {result.get('error')}")
                return False
        else:
            print(f"❌ Errore API: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Esegue tutti i test"""
    print("=" * 70)
    print("🧪 TEST INTEGRAZIONE OR-TOOLS")
    print("=" * 70)
    
    results = []
    
    # Test 1
    results.append(test_health_check())
    
    # Test 2
    results.append(test_optimization_with_sample_data())
    
    # Riepilogo
    print("\n" + "=" * 70)
    print("📋 RIEPILOGO TEST")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passati: {passed}/{total}")
    print(f"❌ Falliti: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 Tutti i test sono passati!")
        sys.exit(0)
    else:
        print("\n⚠️  Alcuni test sono falliti")
        sys.exit(1)


if __name__ == '__main__':
    main()
