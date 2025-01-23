from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class Utilisateur(db.Model):
   __tablename__ = 'utilisateurs'
   id = db.Column(db.Integer, primary_key=True)
   email = db.Column(db.String(120), unique=True, nullable=False)
   mot_de_passe = db.Column(db.String(255), nullable=False)
   role = db.Column(db.String(20), nullable=False)
   date_creation = db.Column(db.DateTime, default=datetime.utcnow)

   def check_password(self, password: str) -> bool:
       return bcrypt.checkpw(password.encode('utf-8'), self.mot_de_passe.encode('utf-8'))

class Parieur(db.Model):
   __tablename__ = 'parieurs'
   id = db.Column(db.Integer, primary_key=True)
   utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), unique=True)
   cagnotte = db.Column(db.Float, default=0.0)
   statut = db.Column(db.String(20), default='actif')
   utilisateur = db.relationship('Utilisateur', backref='parieur', uselist=False)

class Bookmaker(db.Model):
   __tablename__ = 'bookmakers'
   id = db.Column(db.Integer, primary_key=True)
   utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), unique=True)
   numero_employe = db.Column(db.String(50), unique=True, nullable=False)
   statut = db.Column(db.String(20), default='actif')
   utilisateur = db.relationship('Utilisateur', backref='bookmaker', uselist=False)