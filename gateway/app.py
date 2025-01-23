# gateway/app.py
from flask import Flask
from blueprints.auth import auth_bp
from blueprints.match import matches_bp
from blueprints.pari import pari_bp
from blueprints.panier import panier_bp
from blueprints.paiement import paiement_bp

app = Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(matches_bp)
app.register_blueprint(pari_bp)
app.register_blueprint(panier_bp)
app.register_blueprint(paiement_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)