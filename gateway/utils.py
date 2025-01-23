from flask import request, jsonify
import requests
import jwt
import os
from functools import wraps

JWT_SECRET = os.getenv('JWT_SECRET')


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        try:
            token = token.split('Bearer ')[1]
            jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        return f(*args, **kwargs)

    return decorated


def forward_request(service_url, path, method='GET'):
    url = f"{service_url}{path}"
    headers = {key: value for key, value in request.headers if key != 'Host'}
    body = request.get_json() if method in ['POST', 'PUT', 'PATCH'] else None

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=request.args,
            json=body
        )
        return response.content, response.status_code, response.headers.items()
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'Erreur de service: {str(e)}'}), 503, {}


