from flask import Flask, request, jsonify
from models import db
from repository import PanierRepository
import jwt
from datetime import datetime
import os
from dotenv import load_dotenv
import threading
import json
import time
import pika
from utils.rabbitmq import get_rabbitmq_channel
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI_PANIER')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
JWT_SECRET = os.getenv('JWT_SECRET')

db.init_app(app)
panier_repository = PanierRepository()

channel_panier_updates = None
connection_panier_updates = None
channel_pari_updates = None
connection_pari_updates = None


def init_rabbitmq():
    global channel_panier_updates, connection_panier_updates
    global channel_pari_updates, connection_pari_updates
    try:
        channel_panier_updates, connection_panier_updates = get_rabbitmq_channel("panier_updates")
        channel_pari_updates, connection_pari_updates = get_rabbitmq_channel("pari_updates")
    except Exception as e:
        print(f"Erreur connexion RabbitMQ : {e}")
        connection_panier_updates = connection_pari_updates = None
        channel_panier_updates = channel_pari_updates = None


def require_parieur(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        try:
            token = token.split('Bearer ')[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            if payload.get('role') != 'parieur':
                return jsonify({'message': 'Accès non autorisé'}), 403
            return f(*args, **kwargs)
        except:
            return jsonify({'message': 'Token invalide'}), 401

    return decorated


def publish_message(channel, routing_key: str, message: dict):
    if channel:
        try:
            channel.basic_publish(
                exchange='',
                routing_key=routing_key,
                body=json.dumps(message)
            )
            return True
        except:
            init_rabbitmq()
    return False


def keep_alive(connection, interval=30):
    while True:
        try:
            connection.process_data_events(time_limit=1)
        except pika.exceptions.AMQPError:
            break
        time.sleep(interval)


def reconnect(queue_name):
    global channel_panier_updates, connection_panier_updates
    global channel_pari_updates, connection_pari_updates

    while True:
        try:
            if queue_name == 'panier_updates':
                channel_panier_updates, connection_panier_updates = get_rabbitmq_channel("panier_updates")
                threading.Thread(target=keep_alive, args=(connection_panier_updates,), daemon=True).start()
                threading.Thread(target=consume_messages, args=(
                channel_panier_updates, connection_panier_updates, traiter_panier_updates, queue_name),
                                 daemon=True).start()
            elif queue_name == 'pari_updates':
                channel_pari_updates, connection_pari_updates = get_rabbitmq_channel("pari_updates")
                threading.Thread(target=keep_alive, args=(connection_pari_updates,), daemon=True).start()
                threading.Thread(target=consume_messages,
                                 args=(channel_pari_updates, connection_pari_updates, traiter_pari_updates, queue_name),
                                 daemon=True).start()
            break
        except Exception as e:
            print(f"Échec reconnexion RabbitMQ pour {queue_name}: {e}")
            time.sleep(10)


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
        while True:
            try:
                connection.process_data_events(time_limit=1)
                time.sleep(0.1)
            except Exception as e:
                print(f"Erreur consommation {queue_name}: {e}")
                break

    except Exception as e:
        print(f"Erreur configuration {queue_name}: {e}")

    time.sleep(5)
    reconnect(queue_name)


def traiter_panier_updates(ch, method, properties, body):
    with app.app_context():
        try:
            data = json.loads(body)
            print(f"Message reçu panier_updates: {data}")
        except Exception as e:
            print(f"Erreur traitement panier_updates: {e}")


def traiter_pari_updates(ch, method, properties, body):
    with app.app_context():
        try:
            data = json.loads(body)
            print(f"Message reçu pari_updates: {data}")
        except Exception as e:
            print(f"Erreur traitement pari_updates: {e}")


@app.route('/panier', methods=['POST'])
@require_parieur
def creer_panier():
    data = request.json
    token = request.headers.get('Authorization').split('Bearer ')[1]
    payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

    match_ids = [detail['match_id'] for detail in data['paris']]
    if len(match_ids) != len(set(match_ids)):
        return jsonify({'message': 'Un match ne peut pas être sélectionné plusieurs fois'}), 400

    try:
        panier = panier_repository.create_panier(data, payload['user_id'])

        publish_message(channel_panier_updates, 'panier_updates', {
            'type': 'nouveau_panier',
            'panier_id': panier.id,
            'utilisateur_id': panier.utilisateur_id,
            'mise_totale': float(panier.mise_totale)
        })

        return jsonify({'message': 'Panier créé', 'id': panier.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400


@app.route('/panier/<int:panier_id>/validation', methods=['POST'])
@require_parieur
def valider_panier(panier_id):
    token = request.headers.get('Authorization').split('Bearer ')[1]
    payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

    panier = panier_repository.get_panier_by_id(panier_id)

    if panier.utilisateur_id != payload['user_id']:
        return jsonify({'message': 'Accès non autorisé'}), 403

    if not panier_repository.validate_panier(panier):
        return jsonify({'message': 'Ce panier ne peut plus être validé'}), 400

    publish_message(channel_pari_updates, 'pari_updates', {
        'type': 'panier_valide',
        'panier_id': panier.id,
        'utilisateur_id': panier.utilisateur_id,
        'paris': [detail.to_dict() for detail in panier.details],
        'mise_totale': float(panier.mise_totale)
    })

    return jsonify({'message': 'Panier validé'}), 200


@app.route('/panier/utilisateur/<int:utilisateur_id>', methods=['GET'])
@require_parieur
def liste_paniers(utilisateur_id):
    token = request.headers.get('Authorization').split('Bearer ')[1]
    payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

    if payload['user_id'] != utilisateur_id:
        return jsonify({'message': 'Accès non autorisé'}), 403

    paniers = panier_repository.get_paniers_by_user(utilisateur_id)
    return jsonify([p.to_dict() for p in paniers]), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    init_rabbitmq()
    if connection_panier_updates and channel_panier_updates:
        t_keep_alive_panier = threading.Thread(target=keep_alive, args=(connection_panier_updates,), daemon=True)
        t_keep_alive_panier.start()
    else:
        reconnect('panier_updates')

    if connection_pari_updates and channel_pari_updates:
        t_keep_alive_pari = threading.Thread(target=keep_alive, args=(connection_pari_updates,), daemon=True)
        t_keep_alive_pari.start()
    else:
        reconnect('pari_updates')

    app.run(host='0.0.0.0', port=5000)