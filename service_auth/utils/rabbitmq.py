# utils/rabbitmq.py
import pika
import os
import logging
import time

def get_rabbitmq_channel(queue_name):
    rabbitmq_url = os.getenv('RABBITMQ_URL')
    if not rabbitmq_url:
        raise ValueError("La variable d'environnement 'RABBITMQ_URL' n'est pas définie.")

    parameters = pika.URLParameters(rabbitmq_url)
    parameters.heartbeat = 60
    parameters.blocked_connection_timeout = 300

    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            logging.info(f"Connexion à RabbitMQ établie et queue '{queue_name}' déclarée.")
            return channel, connection
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Erreur de connexion à RabbitMQ : {e}. Nouvelle tentative dans 5 secondes.")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Erreur inattendue lors de la connexion à RabbitMQ : {e}")
            raise
