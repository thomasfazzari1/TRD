from flask import Flask, request, jsonify
from models import db
from repository import TransactionRepository
import jwt
from datetime import datetime
import os
from dotenv import load_dotenv
import threading
import json
import time
import requests
import pika
from utils.rabbitmq import get_rabbitmq_channel
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI_PAIEMENT')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
JWT_SECRET = os.getenv('JWT_SECRET')
GATEWAY_URL = 'http://gateway:5000'

db.init_app(app)
transaction_repository = TransactionRepository()

channel_user_updates = None
connection_user_updates = None

def init_rabbitmq():
   global channel_user_updates, connection_user_updates
   try:
       channel_user_updates, connection_user_updates = get_rabbitmq_channel("user_updates")
   except Exception as e:
       connection_user_updates = None
       channel_user_updates = None

def keep_alive(connection, interval=30):
   while True:
       try:
           connection.process_data_events(time_limit=1)
       except pika.exceptions.AMQPError:
           break
       time.sleep(interval)

def reconnect():
   global channel_user_updates, connection_user_updates
   while True:
       try:
           channel_user_updates, connection_user_updates = get_rabbitmq_channel("user_updates")
           threading.Thread(target=keep_alive, args=(connection_user_updates,), daemon=True).start()
           break
       except Exception:
           time.sleep(10)

def require_auth(f):
   @wraps(f)
   def decorated(*args, **kwargs):
       token = request.headers.get('Authorization')
       if not token:
           return jsonify({'message': 'Token manquant'}), 401
       try:
           token = token.split('Bearer ')[1]
           jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
       except:
           return jsonify({'message': 'Token invalide'}), 401
       return f(*args, **kwargs)
   return decorated

@app.route('/transactions/depot', methods=['POST'])
@require_auth
def effectuer_depot():
   data = request.json
   try:
       transaction = transaction_repository.create_transaction(data, 'dépôt')

       message = {
           'type': 'nouveau_depot',
           'utilisateur_id': transaction.utilisateur_id,
           'montant': float(transaction.montant)
       }
       if channel_user_updates:
           try:
               channel_user_updates.basic_publish(
                   exchange='',
                   routing_key='user_updates',
                   body=json.dumps(message)
               )
           except:
               init_rabbitmq()

       response = requests.post(
           f"{GATEWAY_URL}/auth/utilisateur/{transaction.utilisateur_id}/cagnotte/update",
           json={'montant': transaction.montant},
           headers=request.headers
       )

       if response.status_code != 200:
           return jsonify({'message': f"Erreur lors de la mise à jour de la cagnotte: {response.text}"}), 400

       return jsonify({'message': 'Dépôt effectué', 'id': transaction.id}), 201
   except Exception as e:
       db.session.rollback()
       return jsonify({'message': str(e)}), 400

@app.route('/transactions/retrait', methods=['POST'])
@require_auth
def effectuer_retrait():
   data = request.json
   if not data or 'utilisateur_id' not in data or 'montant' not in data:
       return jsonify({'message': 'Champs utilisateur_id et montant requis'}), 400

   try:
       response = requests.get(
           f"{GATEWAY_URL}/auth/utilisateur/{data['utilisateur_id']}/cagnotte",
           headers=request.headers
       )
       if response.status_code != 200:
           return jsonify({'message': 'Impossible de vérifier le solde'}), 400

       solde = response.json().get('cagnotte', 0.0)
       if solde < float(data['montant']):
           return jsonify({'message': 'Solde insuffisant'}), 400

       transaction = transaction_repository.create_transaction(data, 'retrait')

       message = {
           'type': 'nouveau_retrait',
           'utilisateur_id': transaction.utilisateur_id,
           'montant': -float(transaction.montant)
       }
       if channel_user_updates:
           try:
               channel_user_updates.basic_publish(
                   exchange='',
                   routing_key='user_updates',
                   body=json.dumps(message)
               )
           except:
               init_rabbitmq()

       response = requests.post(
           f"{GATEWAY_URL}/auth/utilisateur/{transaction.utilisateur_id}/cagnotte/update",
           json={'montant': -transaction.montant},
           headers=request.headers
       )

       if response.status_code != 200:
           return jsonify({'message': f"Erreur lors de la mise à jour de la cagnotte: {response.text}"}), 400

       return jsonify({'message': 'Retrait effectué', 'id': transaction.id}), 201
   except Exception as e:
       db.session.rollback()
       return jsonify({'message': str(e)}), 400

@app.route('/transactions/gain', methods=['POST'])
def traiter_gain():
   data = request.json
   try:
       data['statut'] = 'validé'
       transaction = transaction_repository.create_transaction(data, 'gain')

       message = {
           'type': 'maj_cagnotte',
           'utilisateur_id': transaction.utilisateur_id,
           'montant': float(transaction.montant)
       }
       if channel_user_updates:
           try:
               channel_user_updates.basic_publish(
                   exchange='',
                   routing_key='user_updates',
                   body=json.dumps(message)
               )
           except:
               init_rabbitmq()

       response = requests.post(
           f"{GATEWAY_URL}/auth/utilisateur/{transaction.utilisateur_id}/cagnotte/update",
           json={'montant': transaction.montant},
           headers=request.headers
       )

       if response.status_code != 200:
           return jsonify({'message': f"Erreur lors de la mise à jour de la cagnotte: {response.text}"}), 400

       return jsonify({'message': 'Gain traité'}), 200
   except Exception as e:
       db.session.rollback()
       return jsonify({'message': str(e)}), 400

@app.route('/transactions/remboursement', methods=['POST'])
def traiter_remboursement():
   data = request.json
   try:
       data['statut'] = 'validé'
       transaction = transaction_repository.create_transaction(data, 'remboursement')

       message = {
           'type': 'maj_cagnotte',
           'utilisateur_id': transaction.utilisateur_id,
           'montant': float(transaction.montant)
       }
       if channel_user_updates:
           try:
               channel_user_updates.basic_publish(
                   exchange='',
                   routing_key='user_updates',
                   body=json.dumps(message)
               )
           except:
               init_rabbitmq()

       response = requests.post(
           f"{GATEWAY_URL}/auth/utilisateur/{transaction.utilisateur_id}/cagnotte/update",
           json={'montant': transaction.montant},
           headers=request.headers
       )

       if response.status_code != 200:
           return jsonify({'message': f"Erreur lors de la mise à jour de la cagnotte: {response.text}"}), 400

       return jsonify({'message': 'Remboursement traité'}), 200
   except Exception as e:
       db.session.rollback()
       return jsonify({'message': str(e)}), 400

@app.route('/transactions/utilisateur/<int:utilisateur_id>', methods=['GET'])
@require_auth
def liste_transactions(utilisateur_id):
   transactions = transaction_repository.get_transactions_by_user(utilisateur_id)
   return jsonify([t.to_dict() for t in transactions]), 200

@app.errorhandler(404)
def not_found(error):
   return jsonify({'message': 'Ressource non trouvée'}), 404

@app.errorhandler(500)
def internal_error(error):
   return jsonify({'message': 'Erreur interne du serveur'}), 500

if __name__ == '__main__':
   with app.app_context():
       db.create_all()

   init_rabbitmq()
   if connection_user_updates and channel_user_updates:
       t_keep_alive = threading.Thread(target=keep_alive, args=(connection_user_updates,), daemon=True)
       t_keep_alive.start()
   else:
       reconnect()

   app.run(host='0.0.0.0', port=5000)