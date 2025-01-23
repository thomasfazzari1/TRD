from models import db, PariGroupe, Pari
from datetime import datetime

class PariRepository:
    def create_pari(self, data: dict, token: str) -> tuple[Pari, str]:
        try:
            nouveau_pari = Pari(
                utilisateur_id=data['utilisateur_id'],
                match_id=data['match_id'],
                type_pari=data['type_pari'],
                montant=data['montant'],
                cote=float(data['cote']),
                gain_potentiel=data['montant'] * float(data['cote'])
            )
            db.session.add(nouveau_pari)
            db.session.commit()
            return nouveau_pari, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    def create_pari_groupe(self, data: dict, token: str) -> tuple[PariGroupe, str]:
        try:
            montant = float(data['montant'])
            cote_totale = 1.0
            paris = []

            for pari_data in data['paris']:
                cote = float(pari_data['cote'])
                cote_totale *= cote
                pari = Pari(
                    utilisateur_id=data['utilisateur_id'],
                    match_id=pari_data['match_id'],
                    type_pari=pari_data['type_pari'],
                    montant=montant,
                    cote=cote,
                    gain_potentiel=montant * cote
                )
                paris.append(pari)

            groupe = PariGroupe(
                utilisateur_id=data['utilisateur_id'],
                montant=montant,
                gain_potentiel=montant * cote_totale,
                paris=paris
            )

            db.session.add(groupe)
            db.session.commit()
            return groupe, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    def get_pari_by_id(self, pari_id: int) -> Pari:
        return Pari.query.get_or_404(pari_id)

    def annuler_pari(self, pari: Pari, motif: str = None) -> bool:
        try:
            pari.annule = True
            pari.motif_annulation = motif
            pari.statut = 'annulé'

            if pari.groupe_id:
                pari.groupe.statut = 'annulé'

            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False

    def get_paris_by_match(self, match_id: int, statut: str = 'en_attente') -> list[Pari]:
        return Pari.query.filter_by(match_id=match_id, statut=statut).all()

    def update_statut_groupe(self, groupe: PariGroupe) -> bool:
        try:
            if any(p.statut == 'perdu' for p in groupe.paris):
                groupe.statut = 'perdu'
            elif all(p.statut == 'gagné' for p in groupe.paris):
                groupe.statut = 'gagné'
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False