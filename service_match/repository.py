from models import db, Match, Cote, Competition, Equipe
from sqlalchemy import or_
from datetime import datetime
import json

class MatchRepository:
    def get_matches(self, competition_id=None, statut=None, equipe_id=None):
        query = Match.query
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        if statut:
            query = query.filter_by(statut=statut)
        if equipe_id:
            query = query.filter(
                or_(Match.equipe_domicile_id == equipe_id,
                    Match.equipe_exterieur_id == equipe_id)
            )
        return query.all()

    def get_match_by_id(self, id: int) -> Match:
        return Match.query.get_or_404(id)

    def get_equipe_by_id(self, id: int) -> Equipe:
        return Equipe.query.get_or_404(id)

    def verify_equipes_match(self, equipe_domicile_id: int, equipe_exterieur_id: int) -> tuple[Equipe, Equipe]:
        equipe_domicile = Equipe.query.get(equipe_domicile_id)
        equipe_exterieur = Equipe.query.get(equipe_exterieur_id)

        if not equipe_domicile or not equipe_exterieur:
            return None, None
        return equipe_domicile, equipe_exterieur

    def creer_match(self, data: dict) -> Match:
        nouveau_match = Match(
            competition_id=data['competition_id'],
            equipe_domicile_id=data['equipe_domicile_id'],
            equipe_exterieur_id=data['equipe_exterieur_id'],
            date_match=datetime.fromisoformat(data['date_match'])
        )

        nouvelle_cote = Cote(
            cote_domicile=data['cote_domicile'],
            cote_nul=data['cote_nul'],
            cote_exterieur=data['cote_exterieur']
        )

        nouveau_match.cotes.append(nouvelle_cote)
        db.session.add(nouveau_match)
        db.session.commit()
        return nouveau_match

    def delete_match(self, match_id: int) -> tuple[bool, str]:
        match = self.get_match_by_id(match_id)

        if match.statut in ['terminé', 'en cours']:
            return False, "Impossible de supprimer un match en cours ou terminé"

        try:
            db.session.delete(match)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def get_competitions(self):
        return Competition.query.all()

    def get_competition_by_id(self, id: int) -> Competition:
        return Competition.query.get_or_404(id)

    def creer_competition(self, data: dict) -> Competition:
        if Competition.query.filter_by(nom=data['nom']).first():
            return None

        nouvelle_competition = Competition(
            nom=data['nom'],
            slug=data['slug'],
            actif=data.get('actif', True)
        )
        db.session.add(nouvelle_competition)
        db.session.commit()
        return nouvelle_competition

    def update_competition(self, competition_id: int, data: dict) -> tuple[Competition, str]:
        competition = self.get_competition_by_id(competition_id)

        if 'nom' in data:
            existing = Competition.query.filter_by(nom=data['nom']).first()
            if existing and existing.id != competition_id:
                return None, "Une compétition avec ce nom existe déjà"
            competition.nom = data['nom']

        if 'slug' in data:
            competition.slug = data['slug']
        if 'actif' in data:
            competition.actif = data['actif']

        try:
            db.session.commit()
            return competition, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    def delete_competition(self, competition_id: int) -> tuple[bool, str]:
        competition = self.get_competition_by_id(competition_id)

        if Match.query.filter_by(competition_id=competition_id).first():
            return False, "Impossible de supprimer une compétition liée à des matches"

        try:
            db.session.delete(competition)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def get_equipes(self):
        return Equipe.query.all()

    def creer_equipe(self, data: dict) -> Equipe:
        if Equipe.query.filter_by(nom=data['nom']).first():
            return None

        nouvelle_equipe = Equipe(nom=data['nom'])
        db.session.add(nouvelle_equipe)
        db.session.commit()
        return nouvelle_equipe

    def update_equipe(self, equipe_id: int, data: dict) -> tuple[Equipe, str]:
        equipe = self.get_equipe_by_id(equipe_id)

        if 'nom' in data:
            existing = Equipe.query.filter_by(nom=data['nom']).first()
            if existing and existing.id != equipe_id:
                return None, "Une équipe avec ce nom existe déjà"
            equipe.nom = data['nom']

        try:
            db.session.commit()
            return equipe, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    def delete_equipe(self, equipe_id: int) -> tuple[bool, str]:
        equipe = self.get_equipe_by_id(equipe_id)

        if Match.query.filter(
                (Match.equipe_domicile_id == equipe_id) |
                (Match.equipe_exterieur_id == equipe_id)
        ).first():
            return False, "Impossible de supprimer une équipe liée à des matches"

        try:
            db.session.delete(equipe)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def update_score(self, match_id: int, data: dict) -> tuple[Match, str]:
        match = self.get_match_by_id(match_id)

        match.score_domicile = data.get('score_domicile', match.score_domicile)
        match.score_exterieur = data.get('score_exterieur', match.score_exterieur)
        match.statut = data.get('statut', match.statut)

        try:
            db.session.commit()
            return match, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    def get_resultat_match(self, match: Match) -> str:
        if match.score_domicile > match.score_exterieur:
            return 'domicile'
        elif match.score_exterieur > match.score_domicile:
            return 'exterieur'
        return 'nul'

    def update_cotes(self, match_id: int, data: dict) -> tuple[Match, str]:
        match = self.get_match_by_id(match_id)

        if not match.cotes:
            return None, "Aucune cote associée à ce match"

        try:
            for cote in match.cotes:
                if 'cote_domicile' in data:
                    cote.cote_domicile = data['cote_domicile']
                if 'cote_nul' in data:
                    cote.cote_nul = data['cote_nul']
                if 'cote_exterieur' in data:
                    cote.cote_exterieur = data['cote_exterieur']
                cote.date_modification = datetime.utcnow()

            db.session.commit()
            return match, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    def traiter_match_update(self, data: dict) -> bool:
        try:
            match = self.get_match_by_id(data['match_id'])
            match.statut = 'terminé'
            match.resultat = data['resultat']
            db.session.commit()
            return True
        except:
            return False