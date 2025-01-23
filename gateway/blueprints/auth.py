from flask import Blueprint, request, jsonify
from utils import forward_request, require_auth
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
SERVICE_URL = os.getenv('AUTH_SERVICE_URL')

@auth_bp.route('/inscription', methods=['POST'])
def inscription():
    return forward_request(SERVICE_URL, '/inscription', 'POST')

@auth_bp.route('/connexion', methods=['POST'])
def connexion():
    return forward_request(SERVICE_URL, '/connexion', 'POST')

@auth_bp.route('/utilisateur/<int:id>/cagnotte', methods=['GET'])
@require_auth
def get_cagnotte(id):
    return forward_request(SERVICE_URL, f'/utilisateur/{id}/cagnotte', 'GET')

@auth_bp.route('/utilisateur/<int:id>/cagnotte/update', methods=['POST'])
@require_auth
def update_cagnotte(id):
    return forward_request(SERVICE_URL, f'/utilisateur/{id}/cagnotte/update', 'POST')
