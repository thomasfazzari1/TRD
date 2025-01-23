# gateway/blueprints/match.py
from flask import Blueprint, request
from utils import forward_request, require_auth
import os

matches_bp = Blueprint('matches', __name__, url_prefix='/matches')
SERVICE_URL = os.getenv('MATCH_SERVICE_URL')


# Matches
@matches_bp.route('', methods=['GET'])
def liste_matches():
    return forward_request(SERVICE_URL, '/matches', 'GET')

@matches_bp.route('', methods=['POST'])
@require_auth
def creer_match():
    return forward_request(SERVICE_URL, '/matches', 'POST')

@matches_bp.route('/<int:match_id>', methods=['DELETE'])
@require_auth
def delete_match(match_id):
    return forward_request(SERVICE_URL, f'/matches/{match_id}', 'DELETE')

@matches_bp.route('/<int:match_id>', methods=['GET'])
def get_match(match_id):
    return forward_request(SERVICE_URL, f'/matches/{match_id}', 'GET')

@matches_bp.route('/<int:match_id>/score', methods=['PUT'])
@require_auth
def update_score(match_id):
    return forward_request(SERVICE_URL, f'/matches/{match_id}/score', 'PUT')

@matches_bp.route('/<int:match_id>/cotes', methods=['PUT'])
@require_auth
def update_cotes(match_id):
    return forward_request(SERVICE_URL, f'/matches/{match_id}/cotes', 'PUT')

# Compétitions
@matches_bp.route('/competitions', methods=['GET'])
def liste_competitions():
    return forward_request(SERVICE_URL, '/matches/competitions', 'GET')

@matches_bp.route('/competitions', methods=['POST'])
@require_auth
def creer_competition():
    return forward_request(SERVICE_URL, '/matches/competitions', 'POST')

@matches_bp.route('/competitions/<int:competition_id>', methods=['PUT'])
@require_auth
def update_competition(competition_id):
    return forward_request(SERVICE_URL, f'/matches/competitions/{competition_id}', 'PUT')

@matches_bp.route('/competitions/<int:competition_id>', methods=['DELETE'])
@require_auth
def delete_competition(competition_id):
    return forward_request(SERVICE_URL, f'/matches/competitions/{competition_id}', 'DELETE')


# Équipes
@matches_bp.route('/equipes', methods=['GET'])
def liste_equipes():
    return forward_request(SERVICE_URL, '/matches/equipes', 'GET')

@matches_bp.route('/equipes', methods=['POST'])
@require_auth
def creer_equipe():
    return forward_request(SERVICE_URL, '/matches/equipes', 'POST')

@matches_bp.route('/equipes/<int:equipe_id>', methods=['PUT'])
@require_auth
def update_equipe(equipe_id):
    return forward_request(SERVICE_URL, f'/matches/equipes/{equipe_id}', 'PUT')

@matches_bp.route('/equipes/<int:equipe_id>', methods=['DELETE'])
@require_auth
def delete_equipe(equipe_id):
    return forward_request(SERVICE_URL, f'/matches/equipes/{equipe_id}', 'DELETE')
