from flask import Flask, request, jsonify
from models import db, Match, Cote, Competition, Equipe
from repository import MatchRepository
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import threading
import json
import time
from utils.rabbitmq import get_rabbitmq_channel
from functools import wraps
from sqlalchemy import or_

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI_MATCH')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
JWT_SECRET = os.getenv('JWT_SECRET')

db.init_app(app)
match_repository = MatchRepository()

channel_match_updates = None
connection_match_updates = None
channel_match_resultats = None
connection_match_resultats = None

def init_rabbitmq():
   global channel_match_updates, connection_match_updates
   global channel_match_resultats, connection_match_resultats
   try:
       channel_match_updates, connection_match_updates = get_rabbitmq_channel("match_updates")
       channel_match_resultats, connection_match_resultats = get_rabbitmq_channel("match_resultats")
   except Exception as e:
       print(f"Échec de la connexion à RabbitMQ : {e}")
       connection_match_updates = connection_match_resultats = None
       channel_match_updates = channel_match_resultats = None

def require_bookmaker(f):
   @wraps(f)
   def decorated(*args, **kwargs):
       token = request.headers.get('Authorization')
       if not token:
           return jsonify({'message': 'Token manquant'}), 401
       try:
           token = token.split('Bearer ')[1]
           payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
           if payload.get('role') != 'bookmaker':
               return jsonify({'message': 'Accès non autorisé'}), 403
       except (jwt.InvalidTokenError, IndexError):
           return jsonify({'message': 'Token invalide'}), 401
       return f(*args, **kwargs)
   return decorated

def traiter_match_updates(ch, method, properties, body):
   with app.app_context():
       try:
           data = json.loads(body)
           match_repository.traiter_match_update(data)
       except Exception as e:
           print(f"Erreur traitement match_updates : {e}")

def consume_messages(channel, connection, callback, queue_name):
   if not channel or not connection:
       print(f"Canal/connexion RabbitMQ indisponible pour {queue_name}")
       return

   try:
       channel.basic_consume(
           queue=queue_name,
           on_message_callback=callback,
           auto_ack=True
       )
       print(f"Démarrage consommation RabbitMQ {queue_name}")
       while True:
           try:
               connection.process_data_events(time_limit=1)
               time.sleep(0.1)
           except Exception as e:
               print(f"Erreur consommation {queue_name} : {e}")
               break
   except Exception as e:
       print(f"Erreur configuration {queue_name} : {e}")

   print(f"Reconnexion RabbitMQ {queue_name} dans 5s...")
   time.sleep(5)
   init_rabbitmq()
   consume_messages(channel, connection, callback, queue_name)

@app.route('/matches', methods=['GET'])
def liste_matches():
   try:
       matches = match_repository.get_matches(
           request.args.get('competition_id'),
           request.args.get('statut'),
           request.args.get('equipe_id')
       )
       return jsonify([match.to_dict() for match in matches]), 200
   except Exception as e:
       return jsonify({'message': str(e)}), 500

@app.route('/matches', methods=['POST'])
@require_bookmaker
def creer_match():
   data = request.json

   if data['equipe_domicile_id'] == data['equipe_exterieur_id']:
       return jsonify({'message': 'Les équipes doivent être différentes'}), 400

   equipe_dom, equipe_ext = match_repository.verify_equipes_match(
       data['equipe_domicile_id'],
       data['equipe_exterieur_id']
   )
   if not equipe_dom or not equipe_ext:
       return jsonify({'message': 'Équipes introuvables'}), 400

   date_match = datetime.fromisoformat(data['date_match'])
   if date_match <= datetime.now():
       return jsonify({'message': 'Date du match doit être future'}), 400

   if data['cote_domicile'] <= 0 or data['cote_nul'] <= 0 or data['cote_exterieur'] <= 0:
       return jsonify({'message': 'Les cotes doivent être positives'}), 400

   try:
       match = match_repository.creer_match(data)
       return jsonify({'message': 'Match créé', 'id': match.id}), 201
   except Exception as e:
       return jsonify({'message': str(e)}), 400

@app.route('/matches/<int:match_id>', methods=['GET'])
def get_match(match_id):
   match = match_repository.get_match_by_id(match_id)
   return jsonify(match.to_dict())

@app.route('/matches/<int:match_id>', methods=['DELETE'])
@require_bookmaker
def delete_match(match_id):
   success, message = match_repository.delete_match(match_id)
   if not success:
       return jsonify({'message': message}), 400
   return jsonify({'message': 'Match supprimé'}), 200

@app.route('/matches/<int:match_id>/score', methods=['PUT'])
@require_bookmaker
def update_score(match_id):
   match, error = match_repository.update_score(match_id, request.json)
   if error:
       return jsonify({'message': error}), 400

   if match.statut == 'terminé':
       resultat = match_repository.get_resultat_match(match)
       try:
           channel_match_resultats.basic_publish(
               exchange='',
               routing_key='match_resultats',
               body=json.dumps({
                   'type': 'match_resultat',
                   'match_id': match.id,
                   'resultat': resultat
               })
           )
       except Exception as e:
           print(f"Erreur publication RabbitMQ: {e}")

   return jsonify({'message': 'Score mis à jour'}), 200

@app.route('/matches/<int:match_id>/cotes', methods=['PUT'])
@require_bookmaker
def update_cotes(match_id):
   data = request.json
   if not data:
       return jsonify({'message': 'Aucune donnée fournie'}), 400

   if ('cote_domicile' in data and data['cote_domicile'] <= 0) or \
      ('cote_nul' in data and data['cote_nul'] <= 0) or \
      ('cote_exterieur' in data and data['cote_exterieur'] <= 0):
       return jsonify({'message': 'Les cotes doivent être positives'}), 400

   match, error = match_repository.update_cotes(match_id, data)
   if error:
       return jsonify({'message': error}), 400

   return jsonify({
       'message': 'Cotes mises à jour',
       'cotes': [cote.to_dict() for cote in match.cotes]
   }), 200

@app.route('/matches/equipes', methods=['GET'])
def liste_equipes():
   equipes = match_repository.get_equipes()
   return jsonify([equipe.to_dict() for equipe in equipes]), 200

@app.route('/matches/equipes', methods=['POST'])
@require_bookmaker
def creer_equipe():
   if not request.json.get('nom'):
       return jsonify({'message': 'Nom requis'}), 400

   equipe = match_repository.creer_equipe(request.json)
   if not equipe:
       return jsonify({'message': 'Équipe déjà existante'}), 400

   return jsonify({'message': 'Équipe créée', 'id': equipe.id}), 201

@app.route('/matches/equipes/<int:equipe_id>', methods=['PUT'])
@require_bookmaker
def update_equipe(equipe_id):
   equipe, error = match_repository.update_equipe(equipe_id, request.json)
   if error:
       return jsonify({'message': error}), 400
   return jsonify({'message': 'Équipe mise à jour'}), 200

@app.route('/matches/equipes/<int:equipe_id>', methods=['DELETE'])
@require_bookmaker
def delete_equipe(equipe_id):
   success, message = match_repository.delete_equipe(equipe_id)
   if not success:
       return jsonify({'message': message}), 400
   return jsonify({'message': 'Équipe supprimée'}), 200

@app.route('/matches/competitions', methods=['GET'])
def liste_competitions():
   competitions = match_repository.get_competitions()
   return jsonify([competition.to_dict() for competition in competitions]), 200

@app.route('/matches/competitions', methods=['POST'])
@require_bookmaker
def creer_competition():
   if not request.json.get('nom') or not request.json.get('slug'):
       return jsonify({'message': 'Nom et slug requis'}), 400

   competition = match_repository.creer_competition(request.json)
   if not competition:
       return jsonify({'message': 'Compétition déjà existante'}), 400

   return jsonify({'message': 'Compétition créée', 'id': competition.id}), 201

@app.route('/matches/competitions/<int:competition_id>', methods=['PUT'])
@require_bookmaker
def update_competition(competition_id):
   competition, error = match_repository.update_competition(competition_id, request.json)
   if error:
       return jsonify({'message': error}), 400
   return jsonify({'message': 'Compétition mise à jour'}), 200

@app.route('/matches/competitions/<int:competition_id>', methods=['DELETE'])
@require_bookmaker
def delete_competition(competition_id):
   success, message = match_repository.delete_competition(competition_id)
   if not success:
       return jsonify({'message': message}), 400
   return jsonify({'message': 'Compétition supprimée'}), 200

if __name__ == '__main__':
   with app.app_context():
       db.create_all()

   init_rabbitmq()
   if connection_match_resultats and channel_match_resultats:
       thread_resultats = threading.Thread(
           target=consume_messages,
           args=(channel_match_resultats, connection_match_resultats, traiter_match_updates, 'match_resultats'),
           daemon=True
       )
       thread_resultats.start()

   if connection_match_updates and channel_match_updates:
       thread_updates = threading.Thread(
           target=consume_messages,
           args=(channel_match_updates, connection_match_updates, traiter_match_updates, 'match_updates'),
           daemon=True
       )
       thread_updates.start()

   app.run(host='0.0.0.0', port=5000)