from flask import Flask, request, jsonify
from models import db
from repository import PariRepository
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
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI_PARI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
JWT_SECRET = os.getenv('JWT_SECRET')
GATEWAY_URL = 'http://gateway:5000'

db.init_app(app)
pari_repository = PariRepository()

channel_pari_updates = None
connection_pari_updates = None
channel_paiement_updates = None
connection_paiement_updates = None
channel_match_resultats = None
connection_match_resultats = None


def init_rabbitmq():
    global channel_pari_updates, connection_pari_updates
    global channel_paiement_updates, connection_paiement_updates
    global channel_match_resultats, connection_match_resultats
    try:
        channel_pari_updates, connection_pari_updates = get_rabbitmq_channel("pari_updates")
        channel_paiement_updates, connection_paiement_updates = get_rabbitmq_channel("paiement_updates")
        channel_match_resultats, connection_match_resultats = get_rabbitmq_channel("match_resultats")
    except Exception as e:
        connection_pari_updates = connection_paiement_updates = connection_match_resultats = None
        channel_pari_updates = channel_paiement_updates = channel_match_resultats = None


def require_parieur(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        try:
            token = token.split('Bearer ')[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            if payload['role'] != 'parieur':
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
    global channel_pari_updates, connection_pari_updates
    global channel_paiement_updates, connection_paiement_updates
    global channel_match_resultats, connection_match_resultats

    while True:
        try:
            if queue_name == 'pari_updates':
                channel_pari_updates, connection_pari_updates = get_rabbitmq_channel("pari_updates")
            elif queue_name == 'paiement_updates':
                channel_paiement_updates, connection_paiement_updates = get_rabbitmq_channel("paiement_updates")
            elif queue_name == 'match_resultats':
                channel_match_resultats, connection_match_resultats = get_rabbitmq_channel("match_resultats")

            connection = locals().get(f"connection_{queue_name}")
            if connection:
                threading.Thread(target=keep_alive, args=(connection,), daemon=True).start()
            break
        except Exception as e:
            print(f"Échec reconnexion {queue_name}: {e}")
            time.sleep(10)


@app.route('/paris', methods=['POST'])
@require_parieur
def placer_pari():
    data = request.json
    token = request.headers.get('Authorization')
    payload = jwt.decode(token.replace('Bearer ', ''), JWT_SECRET, algorithms=['HS256'])

    resp_match = requests.get(f"{GATEWAY_URL}/matches/{data['match_id']}", headers=request.headers)
    if resp_match.status_code != 200:
        return jsonify({'message': 'Match introuvable'}), 404

    match = resp_match.json()
    if match['statut'] != 'à_venir':
        return jsonify({'message': 'Paris impossible sur ce match'}), 400

    try:
        date_match = datetime.fromisoformat(match['date_match'])
        if date_match <= datetime.now():
            return jsonify({'message': 'Match déjà passé'}), 400

        resp_cagnotte = requests.get(
            f"{GATEWAY_URL}/auth/utilisateur/{payload['user_id']}/cagnotte",
            headers=request.headers
        )
        if resp_cagnotte.status_code != 200:
            return jsonify({'message': 'Erreur vérification cagnotte'}), 400

        cagnotte = resp_cagnotte.json()['cagnotte']
        montant = float(data['montant'])
        if cagnotte < montant:
            return jsonify({'message': 'Cagnotte insuffisante'}), 400

        retrait_resp = requests.post(
            f"{GATEWAY_URL}/transactions/retrait",
            json={
                "utilisateur_id": payload['user_id'],
                "montant": montant
            },
            headers=request.headers
        )
        if retrait_resp.status_code != 201:
            return jsonify({'message': 'Échec du retrait'}), 400

        data['utilisateur_id'] = payload['user_id']
        nouveau_pari, error = pari_repository.create_pari(data, token)
        if error:
            return jsonify({'message': error}), 400

        publish_message(channel_pari_updates, 'pari_updates', {
            'type': 'nouveau_pari',
            'pari_id': nouveau_pari.id,
            'utilisateur_id': nouveau_pari.utilisateur_id,
            'match_id': nouveau_pari.match_id,
            'montant': float(nouveau_pari.montant),
            'gain_potentiel': float(nouveau_pari.gain_potentiel)
        })

        return jsonify({'message': 'Pari placé', 'id': nouveau_pari.id}), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 400


@app.route('/paris/groupe', methods=['POST'])
@require_parieur
def placer_pari_combine():
    data = request.json
    token = request.headers.get('Authorization')
    payload = jwt.decode(token.replace('Bearer ', ''), JWT_SECRET, algorithms=['HS256'])

    try:
        resp_cagnotte = requests.get(
            f"{GATEWAY_URL}/auth/utilisateur/{payload['user_id']}/cagnotte",
            headers=request.headers
        )
        if resp_cagnotte.status_code != 200:
            return jsonify({'message': 'Erreur vérification cagnotte'}), 400

        cagnotte = resp_cagnotte.json()['cagnotte']
        montant = float(data['montant'])
        if cagnotte < montant:
            return jsonify({'message': 'Cagnotte insuffisante'}), 400

        # Vérifier validité des matchs
        for pari in data['paris']:
            resp_match = requests.get(
                f"{GATEWAY_URL}/matches/{pari['match_id']}",
                headers=request.headers
            )
            if resp_match.status_code != 200:
                return jsonify({'message': f"Match {pari['match_id']} introuvable"}), 404

            match = resp_match.json()
            if match['statut'] != 'à_venir':
                return jsonify({'message': f"Match {pari['match_id']} non disponible"}), 400

            date_match = datetime.fromisoformat(match['date_match'])
            if date_match <= datetime.now():
                return jsonify({'message': f"Match {pari['match_id']} déjà passé"}), 400

        retrait_resp = requests.post(
            f"{GATEWAY_URL}/transactions/retrait",
            json={
                "utilisateur_id": payload['user_id'],
                "montant": montant
            },
            headers=request.headers
        )
        if retrait_resp.status_code != 201:
            return jsonify({'message': 'Échec du retrait'}), 400

        data['utilisateur_id'] = payload['user_id']
        groupe, error = pari_repository.create_pari_groupe(data, token)
        if error:
            return jsonify({'message': error}), 400

        publish_message(channel_pari_updates, 'pari_updates', {
            'type': 'nouveau_pari_groupe',
            'groupe_id': groupe.id,
            'utilisateur_id': groupe.utilisateur_id,
            'montant': float(groupe.montant),
            'gain_potentiel': float(groupe.gain_potentiel)
        })

        return jsonify({'message': 'Pari combiné placé', 'id': groupe.id}), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 400


@app.route('/paris/<int:pari_id>/annulation', methods=['POST'])
@require_parieur
def annuler_pari(pari_id):
    token = request.headers.get('Authorization')
    payload = jwt.decode(token.replace('Bearer ', ''), JWT_SECRET, algorithms=['HS256'])

    pari = pari_repository.get_pari_by_id(pari_id)
    if pari.utilisateur_id != payload['user_id']:
        return jsonify({'message': 'Accès non autorisé'}), 403

    if pari.statut != 'en_attente':
        return jsonify({'message': "Impossible d'annuler ce pari"}), 400

    delai = datetime.utcnow() - pari.date_creation
    if delai > timedelta(minutes=30):
        return jsonify({'message': "Délai d'annulation dépassé"}), 400

    try:
        if not pari_repository.annuler_pari(pari, request.json.get('motif')):
            return jsonify({'message': "Erreur lors de l'annulation"}), 400

        remboursement_resp = requests.post(
            f"{GATEWAY_URL}/transactions/remboursement",
            json={
                "utilisateur_id": pari.utilisateur_id,
                "montant": float(pari.montant)
            },
            headers=request.headers
        )
        if remboursement_resp.status_code != 200:
            return jsonify({'message': 'Échec du remboursement'}), 400

        return jsonify({'message': 'Pari annulé et remboursé'}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 400


def traiter_resultat(ch, method, properties, body):
    with app.app_context():
        try:
            data = json.loads(body)
            paris = pari_repository.get_paris_by_match(data['match_id'])

            for pari in paris:
                statut = 'gagné' if pari.type_pari == data['resultat'] else 'perdu'
                pari.statut = statut

                if statut == 'gagné':
                    publish_message(channel_paiement_updates, 'paiement_updates', {
                        'type': 'gain_pari',
                        'utilisateur_id': pari.utilisateur_id,
                        'montant': float(pari.gain_potentiel)
                    })

                if pari.groupe_id and pari_repository.update_statut_groupe(pari.groupe):
                    groupe = pari.groupe
                    if groupe.statut == 'gagné':
                        publish_message(channel_paiement_updates, 'paiement_updates', {
                            'type': 'gain_pari_groupe',
                            'utilisateur_id': groupe.utilisateur_id,
                            'montant': float(groupe.gain_potentiel)
                        })

            db.session.commit()
        except Exception as e:
            print(f"Erreur traitement résultat: {e}")


def consume_messages(channel, connection, callback, queue_name):
    if not channel or not connection:
        print(f"Canal/connexion indisponible pour {queue_name}")
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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    init_rabbitmq()
    if connection_match_resultats and channel_match_resultats:
        threading.Thread(
            target=consume_messages,
            args=(channel_match_resultats, connection_match_resultats, traiter_resultat, 'match_resultats'),
            daemon=True
        ).start()
    else:
        reconnect('match_resultats')

    app.run(host='0.0.0.0', port=5000)