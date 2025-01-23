from flask import Flask, request, jsonify
import jwt
import bcrypt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import threading
import time
import json
from models import db, Utilisateur, Parieur, Bookmaker
from repository import AuthRepository
from utils.rabbitmq import get_rabbitmq_channel

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI_AUTH')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
JWT_SECRET = os.getenv('JWT_SECRET')

db.init_app(app)
auth_repository = AuthRepository()

channel_user_updates = None
connection_user_updates = None

def init_rabbitmq():
   global channel_user_updates, connection_user_updates
   try:
       channel_user_updates, connection_user_updates = get_rabbitmq_channel("user_updates")
   except Exception as e:
       print(f"Échec de la connexion à RabbitMQ : {e}")
       connection_user_updates = None
       channel_user_updates = None

def traiter_user_updates(ch, method, properties, body):
   with app.app_context():
       try:
           data = json.loads(body)
           auth_repository.traiter_user_updates(data)
       except Exception as e:
           print(f"Erreur lors du traitement du message RabbitMQ : {str(e)}")

def consume_messages():
   if not channel_user_updates or not connection_user_updates:
       print("Le canal ou la connexion RabbitMQ n'est pas disponible.")
       return

   try:
       channel_user_updates.basic_consume(
           queue='user_updates',
           on_message_callback=traiter_user_updates,
           auto_ack=True
       )
       print("Démarrage de la consommation des messages RabbitMQ...")
       while True:
           try:
               connection_user_updates.process_data_events(time_limit=1)
               time.sleep(0.1)
           except Exception as e:
               print(f"Erreur pendant la consommation des messages : {e}")
               break
   except Exception as e:
       print(f"Erreur lors de la configuration de la consommation des messages : {e}")

   print("Tentative de reconnexion à RabbitMQ dans 5 secondes...")
   time.sleep(5)
   init_rabbitmq()
   consume_messages()

@app.route('/inscription', methods=['POST'])
def inscription():
   data = request.get_json()
   if auth_repository.get_utilisateur_by_email(data['email']):
       return jsonify({'message': 'Email déjà utilisé'}), 400

   try:
       auth_repository.creer_utilisateur(data)
       db.session.commit()
       return jsonify({'message': 'Inscription réussie'}), 201
   except Exception as e:
       db.session.rollback()
       return jsonify({'message': f'Erreur: {str(e)}'}), 400

@app.route('/connexion', methods=['POST'])
def connexion():
   data = request.get_json()
   utilisateur = auth_repository.get_utilisateur_by_email(data['email'])

   if not utilisateur or not bcrypt.checkpw(
           data['mot_de_passe'].encode('utf-8'),
           utilisateur.mot_de_passe.encode('utf-8')
   ):
       return jsonify({'message': 'Identifiants invalides'}), 401

   token = jwt.encode({
       'user_id': utilisateur.id,
       'email': utilisateur.email,
       'role': utilisateur.role,
       'exp': datetime.utcnow() + timedelta(days=1)
   }, JWT_SECRET)

   return jsonify({
       'token': token,
       'user': {
           'id': utilisateur.id,
           'email': utilisateur.email,
           'role': utilisateur.role
       }
   })

@app.route('/utilisateur/profil', methods=['GET'])
def profil():
   token = request.headers.get('Authorization', '').replace('Bearer ', '')
   try:
       payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
       utilisateur = auth_repository.get_utilisateur_by_id(payload['user_id'])

       if not utilisateur:
           return jsonify({'message': 'Utilisateur non trouvé'}), 404

       profil_data = {
           'id': utilisateur.id,
           'email': utilisateur.email,
           'role': utilisateur.role
       }

       if utilisateur.role == 'parieur':
           parieur = auth_repository.get_parieur_by_utilisateur_id(utilisateur.id)
           profil_data['cagnotte'] = parieur.cagnotte
           profil_data['statut'] = parieur.statut
       elif utilisateur.role == 'bookmaker':
           bookmaker = auth_repository.get_bookmaker_by_utilisateur_id(utilisateur.id)
           profil_data['numero_employe'] = bookmaker.numero_employe
           profil_data['statut'] = bookmaker.statut

       return jsonify(profil_data)
   except jwt.InvalidTokenError:
       return jsonify({'message': 'Token invalide'}), 401

@app.route('/utilisateur/<int:id>/cagnotte', methods=['GET'])
def get_cagnotte(id):
   response, status_code = auth_repository.get_cagnotte_by_id(id)
   return jsonify(response), status_code

@app.route('/utilisateur/<int:id>/cagnotte/update', methods=['POST'])
def update_cagnotte(id):
   data = request.get_json()
   if 'montant' not in data:
       return jsonify({'message': 'Montant requis'}), 400

   try:
       parieur, error = auth_repository.update_cagnotte(id, float(data['montant']))
       if error:
           return jsonify({'message': error}), 404 if 'non trouvé' in error else 400
       return jsonify({'message': 'Cagnotte mise à jour', 'cagnotte': parieur.cagnotte}), 200
   except ValueError:
       return jsonify({'message': 'Montant invalide'}), 400
   except Exception as e:
       return jsonify({'message': f'Erreur lors de la mise à jour : {str(e)}'}), 500

if __name__ == '__main__':
   with app.app_context():
       db.create_all()

   init_rabbitmq()
   if connection_user_updates and channel_user_updates:
       consumer_thread = threading.Thread(target=consume_messages, daemon=True)
       consumer_thread.start()
   else:
       print("Impossible de démarrer le thread RabbitMQ.")

   app.run(host='0.0.0.0', port=5000)