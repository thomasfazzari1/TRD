# gateway/blueprints/pari.py
from flask import Blueprint
from utils import forward_request, require_auth
import os

pari_bp = Blueprint('paris', __name__, url_prefix='/paris')
SERVICE_URL = os.getenv('PARI_SERVICE_URL')

@pari_bp.route('/', methods=['POST'])
@require_auth
def placer_pari():
   return forward_request(SERVICE_URL, '/paris', 'POST')

@pari_bp.route('/utilisateur/<int:utilisateur_id>', methods=['GET'])
@require_auth
def liste_paris_utilisateur(utilisateur_id):
   return forward_request(SERVICE_URL, f'/paris/utilisateur/{utilisateur_id}', 'GET')

@pari_bp.route('/groupe', methods=['POST'])
@require_auth
def placer_pari_combine():
    return forward_request(SERVICE_URL, '/paris/groupe', 'POST')

@pari_bp.route('/<int:pari_id>/annulation', methods=['POST'])
@require_auth
def annuler_pari(pari_id):
    return forward_request(SERVICE_URL, f'/paris/{pari_id}/annulation', 'POST')

