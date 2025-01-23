from models import db, PanierPari, PanierParisDetail
from datetime import datetime


class PanierRepository:
    def create_panier(self, data: dict, utilisateur_id: int) -> PanierPari:
        panier = PanierPari(
            utilisateur_id=utilisateur_id,
            type_pari=data['type_pari'],
            mise_totale=data['mise_totale']
        )

        for detail in data['paris']:
            panier_detail = PanierParisDetail(
                match_id=detail['match_id'],
                pronostic=detail['pronostic'],
                cote=detail['cote']
            )
            panier.details.append(panier_detail)

        db.session.add(panier)
        db.session.commit()
        return panier

    def get_panier_by_id(self, panier_id: int) -> PanierPari:
        return PanierPari.query.get_or_404(panier_id)

    def get_paniers_by_user(self, utilisateur_id: int) -> list[PanierPari]:
        return PanierPari.query.filter_by(utilisateur_id=utilisateur_id).all()

    def validate_panier(self, panier: PanierPari) -> bool:
        if panier.statut != 'en_cours':
            return False

        panier.statut = 'validé'
        db.session.commit()
        return True