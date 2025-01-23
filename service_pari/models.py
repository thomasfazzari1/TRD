from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PariGroupe(db.Model):
   __tablename__ = 'paris_groupes'
   id = db.Column(db.Integer, primary_key=True)
   utilisateur_id = db.Column(db.Integer, nullable=False)
   montant = db.Column(db.Float(precision=2), nullable=False)
   gain_potentiel = db.Column(db.Float(precision=2), nullable=False)
   statut = db.Column(db.String(20), default='en_attente')
   date_creation = db.Column(db.DateTime, default=datetime.utcnow)
   paris = db.relationship('Pari', backref='groupe', lazy=True)

   def to_dict(self):
       return {
           'id': self.id,
           'utilisateur_id': self.utilisateur_id,
           'montant': float(self.montant),
           'gain_potentiel': float(self.gain_potentiel),
           'statut': self.statut,
           'date_creation': self.date_creation.isoformat(),
           'paris': [pari.to_dict() for pari in self.paris]
       }

class Pari(db.Model):
   __tablename__ = 'paris'
   id = db.Column(db.Integer, primary_key=True)
   utilisateur_id = db.Column(db.Integer, nullable=False)
   match_id = db.Column(db.Integer, nullable=False)
   type_pari = db.Column(db.String(20), nullable=False)
   montant = db.Column(db.Float(precision=2), nullable=False)
   cote = db.Column(db.Float(precision=2), nullable=False)
   gain_potentiel = db.Column(db.Float(precision=2), nullable=False)
   statut = db.Column(db.String(20), default='en_attente')
   date_creation = db.Column(db.DateTime, default=datetime.utcnow)
   groupe_id = db.Column(db.Integer, db.ForeignKey('paris_groupes.id'), nullable=True)
   annule = db.Column(db.Boolean, default=False)
   motif_annulation = db.Column(db.String(200))

   def to_dict(self):
       return {
           'id': self.id,
           'utilisateur_id': self.utilisateur_id,
           'match_id': self.match_id,
           'type_pari': self.type_pari,
           'montant': float(self.montant),
           'cote': float(self.cote),
           'gain_potentiel': float(self.gain_potentiel),
           'statut': self.statut,
           'date_creation': self.date_creation.isoformat(),
           'groupe_id': self.groupe_id,
           'annule': self.annule,
           'motif_annulation': self.motif_annulation
       }