"""
API Flask per l'ottimizzazione dei ritiri con OR-Tools
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from optimizer import optimize_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permetti richieste da qualsiasi origine


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'OR-Tools Route Optimizer',
        'version': '1.0.0'
    })


@app.route('/api/optimize', methods=['POST'])
def optimize():
    """
    Endpoint principale per l'ottimizzazione
    
    Request body:
    {
        "stops": [...],
        "morningVehicles": [...],
        "afternoonVehicles": [...],
        "timeWindows": ["mattino", "pomeriggio"]
    }
    
    Response:
    {
        "success": true,
        "data": {
            "morningRoutes": [...],
            "afternoonRoutes": [...],
            "unassigned": [...]
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Nessun dato ricevuto'
            }), 400
        
        # Validazione base
        required_fields = ['stops', 'timeWindows']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo obbligatorio mancante: {field}'
                }), 400
        
        logger.info(f"Richiesta ottimizzazione: {len(data.get('stops', []))} stops, "
                   f"Time windows: {data.get('timeWindows')}")
        
        # Esegui ottimizzazione
        result = optimize_routes(data)
        
        # Statistiche
        total_routes = len(result['morningRoutes']) + len(result['afternoonRoutes'])
        total_assigned = sum(
            len(route['stops']) 
            for route in result['morningRoutes'] + result['afternoonRoutes']
        )
        total_unassigned = len(result['unassigned'])
        
        logger.info(f"Ottimizzazione completata: {total_routes} routes, "
                   f"{total_assigned} assigned, {total_unassigned} unassigned")
        
        return jsonify({
            'success': True,
            'data': result,
            'stats': {
                'totalRoutes': total_routes,
                'totalAssigned': total_assigned,
                'totalUnassigned': total_unassigned
            }
        })
        
    except Exception as e:
        logger.error(f"Errore durante ottimizzazione: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/test', methods=['POST'])
def test_optimization():
    """
    Endpoint di test con dati di esempio
    """
    # Dati di esempio
    test_data = {
        "stops": [
            {
                "key": "Ceramica A",
                "name": "Ceramica A",
                "coords": [44.55, 10.78],
                "totalWeight": 1500,
                "orders": [{"cliente": "Cliente 1", "peso": 1500}],
                "loadingTime": 20,
                "zone": "FIORANO 1",
                "priorityScore": 0,
                "readyTime": "mattino",
                "appointment": None,
                "appointmentTime": None,
                "openingWindows": [{"start": 480, "end": 720}]
            },
            {
                "key": "Ceramica B",
                "name": "Ceramica B",
                "coords": [44.52, 10.75],
                "totalWeight": 2000,
                "orders": [{"cliente": "Cliente 2", "peso": 2000}],
                "loadingTime": 25,
                "zone": "SASSUOLO 1",
                "priorityScore": 2,
                "readyTime": "mattino",
                "appointment": "2024-01-15",
                "appointmentTime": "10:00",
                "openingWindows": [{"start": 480, "end": 720}]
            },
            {
                "key": "Ceramica C",
                "name": "Ceramica C",
                "coords": [44.50, 10.80],
                "totalWeight": 1800,
                "orders": [{"cliente": "Cliente 3", "peso": 1800}],
                "loadingTime": 22,
                "zone": "FIORANO 2",
                "priorityScore": 0,
                "readyTime": "pomeriggio",
                "appointment": None,
                "appointmentTime": None,
                "openingWindows": [{"start": 840, "end": 1080}]
            }
        ],
        "morningVehicles": [
            {
                "id": "v1",
                "targa": "AB123CD",
                "autista": "Mario Rossi",
                "payload": 5000,
                "rules": {"maxStops": None, "mandatoryCeramics": []}
            }
        ],
        "afternoonVehicles": [
            {
                "id": "v2",
                "targa": "EF456GH",
                "autista": "Luigi Verdi",
                "payload": 4000,
                "rules": {"maxStops": None, "mandatoryCeramics": []}
            }
        ],
        "timeWindows": ["mattino", "pomeriggio"]
    }
    
    try:
        result = optimize_routes(test_data)
        
        return jsonify({
            'success': True,
            'message': 'Test completato',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Errore nel test: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint non trovato'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Errore interno del server'
    }), 500


if __name__ == '__main__':
    logger.info("Avvio API Flask su porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
