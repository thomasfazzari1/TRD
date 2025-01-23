# service_match/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Equipe(db.Model):
    __tablename__ = 'equipes'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    matchs_domicile = db.relationship(
        'Match',
        foreign_keys='Match.equipe_domicile_id',
        back_populates='equipe_domicile',
        lazy=True
    )
    matchs_exterieur = db.relationship(
        'Match',
        foreign_keys='Match.equipe_exterieur_id',
        back_populates='equipe_exterieur',
        lazy=True
    )

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'date_creation': self.date_creation.isoformat()
        }


class Competition(db.Model):
    __tablename__ = 'competitions'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    matches = db.relationship('Match', back_populates='competition', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'slug': self.slug,
            'actif': self.actif,
            'date_creation': self.date_creation.isoformat()
        }


class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    equipe_domicile_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)
    equipe_exterieur_id = db.Column(db.Integer, db.ForeignKey('equipes.id'), nullable=False)
    date_match = db.Column(db.DateTime, nullable=False)
    statut = db.Column(db.String(20), default='à_venir')
    score_domicile = db.Column(db.Integer)
    score_exterieur = db.Column(db.Integer)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    competition = db.relationship('Competition', back_populates='matches')
    equipe_domicile = db.relationship(
        'Equipe',
        foreign_keys=[equipe_domicile_id],
        back_populates='matchs_domicile'
    )
    equipe_exterieur = db.relationship(
        'Equipe',
        foreign_keys=[equipe_exterieur_id],
        back_populates='matchs_exterieur'
    )
    cotes = db.relationship('Cote', back_populates='match', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'competition': self.competition.to_dict(),
            'equipe_domicile': self.equipe_domicile.to_dict(),
            'equipe_exterieur': self.equipe_exterieur.to_dict(),
            'date_match': self.date_match.isoformat(),
            'statut': self.statut,
            'score_domicile': self.score_domicile,
            'score_exterieur': self.score_exterieur,
            'date_creation': self.date_creation.isoformat(),
            'cotes': [cote.to_dict() for cote in self.cotes]
        }


class Cote(db.Model):
    __tablename__ = 'cotes'

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    cote_domicile = db.Column(db.Float, nullable=False)
    cote_nul = db.Column(db.Float, nullable=False)
    cote_exterieur = db.Column(db.Float, nullable=False)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow)

    match = db.relationship('Match', back_populates='cotes')

    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'cote_domicile': self.cote_domicile,
            'cote_nul': self.cote_nul,
            'cote_exterieur': self.cote_exterieur,
            'date_modification': self.date_modification.isoformat()
        }
