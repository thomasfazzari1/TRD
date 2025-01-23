# gateway/blueprints/paiement.py
from flask import Blueprint
from utils import forward_request, require_auth
import os

paiement_bp = Blueprint('paiement', __name__, url_prefix='/transactions')
SERVICE_URL = os.getenv('PAIEMENT_SERVICE_URL')

@paiement_bp.route('/depot', methods=['POST'])
@require_auth
def effectuer_depot():
   return forward_request(SERVICE_URL, '/transactions/depot', 'POST')

@paiement_bp.route('/gain', methods=['POST'])
@require_auth
def traiter_gain():
    return forward_request(SERVICE_URL, '/transactions/gain', 'POST')

@paiement_bp.route('/remboursement', methods=['POST'])
@require_auth
def traiter_remboursement():
    return forward_request(SERVICE_URL, '/transactions/remboursement', 'POST')


@paiement_bp.route('/retrait', methods=['POST'])
@require_auth
def effectuer_retrait():
    return forward_request(SERVICE_URL, '/transactions/retrait', 'POST')

@paiement_bp.route('/utilisateur/<int:utilisateur_id>', methods=['GET'])
@require_auth
def liste_transactions(utilisateur_id):
   return forward_request(SERVICE_URL, f'/transactions/utilisateur/{utilisateur_id}', 'GET')
