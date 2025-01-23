from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PanierPari(db.Model):
   __tablename__ = 'panier_paris'
   id = db.Column(db.Integer, primary_key=True)
   utilisateur_id = db.Column(db.Integer, nullable=False)
   type_pari = db.Column(db.String(20), nullable=False)
   mise_totale = db.Column(db.Float, nullable=False)
   statut = db.Column(db.String(20), default='en_cours')
   date_creation = db.Column(db.DateTime, default=datetime.utcnow)
   details = db.relationship('PanierParisDetail', backref='panier', lazy=True)

   def to_dict(self):
       return {
           'id': self.id,
           'utilisateur_id': self.utilisateur_id,
           'type_pari': self.type_pari,
           'mise_totale': float(self.mise_totale),
           'statut': self.statut,
           'date_creation': self.date_creation.isoformat(),
           'details': [detail.to_dict() for detail in self.details]
       }

class PanierParisDetail(db.Model):
   __tablename__ = 'panier_paris_details'
   id = db.Column(db.Integer, primary_key=True)
   panier_id = db.Column(db.Integer, db.ForeignKey('panier_paris.id'), nullable=False)
   match_id = db.Column(db.Integer, nullable=False)
   pronostic = db.Column(db.String(20), nullable=False)
   cote = db.Column(db.Float, nullable=False)

   def to_dict(self):
       return {
           'match_id': self.match_id,
           'pronostic': self.pronostic, 
           'cote': float(self.cote)
       }