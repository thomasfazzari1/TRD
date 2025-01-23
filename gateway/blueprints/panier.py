# gateway/blueprints/panier.py
from flask import Blueprint
from utils import forward_request, require_auth
import os

panier_bp = Blueprint('panier', __name__, url_prefix='/panier')
SERVICE_URL = os.getenv('PANIER_SERVICE_URL')

@panier_bp.route('/', methods=['POST'])
@require_auth
def creer_panier():
   return forward_request(SERVICE_URL, '/panier', 'POST')

@panier_bp.route('/<int:panier_id>/validation', methods=['POST'])
@require_auth
def valider_panier(panier_id):
   return forward_request(SERVICE_URL, f'/panier/{panier_id}/validation', 'POST')

@panier_bp.route('/utilisateur/<int:utilisateur_id>', methods=['GET'])
@require_auth
def liste_paniers(utilisateur_id):
   return forward_request(SERVICE_URL, f'/panier/utilisateur/{utilisateur_id}', 'GET')
