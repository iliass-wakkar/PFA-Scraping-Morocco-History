from flask import Blueprint, jsonify, request, make_response
from services.historical_events_service import HistoricalEventsService

historical_events_bp = Blueprint('historical_events', __name__)
historical_events_service = HistoricalEventsService()

def add_cors_headers(response):
    """Add CORS headers to response"""
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@historical_events_bp.route('/', methods=['OPTIONS'])
@historical_events_bp.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path=None):
    """Handle OPTIONS requests for CORS preflight"""
    response = make_response()
    return add_cors_headers(response)

@historical_events_bp.route('/', methods=['GET'])
def get_all_events():
    """Get all historical events"""
    try:
        language = request.args.get('language', 'ar')
        events = historical_events_service.get_all_events(language)
        response = jsonify({"status": "success", "data": events})
        return add_cors_headers(response)
    except Exception as e:
        response = jsonify({"status": "error", "message": str(e)}), 500
        return add_cors_headers(response[0]), response[1]

@historical_events_bp.route('/<period_name>', methods=['GET'])
def get_events_by_period(period_name):
    """Get events for a specific period"""
    try:
        language = request.args.get('language', 'ar')
        events = historical_events_service.get_events_by_period(period_name, language)
        response = jsonify({"status": "success", "data": events})
        return add_cors_headers(response)
    except Exception as e:
        response = jsonify({"status": "error", "message": str(e)}), 500
        return add_cors_headers(response[0]), response[1]

@historical_events_bp.route('/search', methods=['GET'])
def search_events():
    """Search events by query"""
    try:
        query = request.args.get('q', '')
        language = request.args.get('language', 'ar')
        events = historical_events_service.search_events(query, language)
        response = jsonify({"status": "success", "data": events})
        return add_cors_headers(response)
    except Exception as e:
        response = jsonify({"status": "error", "message": str(e)}), 500
        return add_cors_headers(response[0]), response[1] 