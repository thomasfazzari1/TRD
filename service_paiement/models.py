from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Transaction(db.Model):
   __tablename__ = 'transactions'
   id = db.Column(db.Integer, primary_key=True)
   utilisateur_id = db.Column(db.Integer, nullable=False)
   type_transaction = db.Column(db.String(50), nullable=False) 
   montant = db.Column(db.Float, nullable=False)
   reference = db.Column(db.String(50), unique=True, nullable=False)
   statut = db.Column(db.String(20), default='en_attente')
   date_creation = db.Column(db.DateTime, server_default=db.func.now())

   def __repr__(self):
       return f"<Transaction {self.id}>"

   def to_dict(self):
       return {
           'id': self.id,
           'utilisateur_id': self.utilisateur_id,
           'type_transaction': self.type_transaction,
           'montant': float(self.montant),
           'reference': self.reference,
           'statut': self.statut,
           'date_creation': self.date_creation.isoformat()
       }