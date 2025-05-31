from flask import Blueprint, jsonify, request
from services.historical_events_service import HistoricalEventsService

historical_events_bp = Blueprint('historical_events', __name__)
historical_events_service = HistoricalEventsService()

@historical_events_bp.route('/', methods=['GET'])
def get_all_events():
    """Get all historical events"""
    try:
        language = request.args.get('language', 'ar')
        events = historical_events_service.get_all_events(language)
        return jsonify({"status": "success", "data": events})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@historical_events_bp.route('/<period_name>', methods=['GET'])
def get_events_by_period(period_name):
    """Get events for a specific period"""
    try:
        language = request.args.get('language', 'ar')
        events = historical_events_service.get_events_by_period(period_name, language)
        return jsonify({"status": "success", "data": events})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@historical_events_bp.route('/search', methods=['GET'])
def search_events():
    """Search events by query"""
    try:
        query = request.args.get('q', '')
        language = request.args.get('language', 'ar')
        events = historical_events_service.search_events(query, language)
        return jsonify({"status": "success", "data": events})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500 