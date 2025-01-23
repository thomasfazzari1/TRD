from models import db, Utilisateur, Parieur, Bookmaker
import bcrypt
import json
from datetime import datetime

class AuthRepository:
    def get_utilisateur_by_email(self, email: str) -> Utilisateur:
        return Utilisateur.query.filter_by(email=email).first()

    def get_utilisateur_by_id(self, id: int) -> Utilisateur:
        return Utilisateur.query.get(id)

    def get_parieur_by_utilisateur_id(self, utilisateur_id: int) -> Parieur:
        return Parieur.query.filter_by(utilisateur_id=utilisateur_id).first()

    def get_bookmaker_by_utilisateur_id(self, utilisateur_id: int) -> Bookmaker:
        return Bookmaker.query.filter_by(utilisateur_id=utilisateur_id).first()

    def get_cagnotte_by_id(self, id: int) -> dict:
        utilisateur = self.get_utilisateur_by_id(id)
        if not utilisateur:
            return {"message": "Utilisateur non trouvé"}, 404

        if utilisateur.role != "parieur":
            return {"message": "Non autorisé"}, 403

        parieur = self.get_parieur_by_utilisateur_id(id)
        if not parieur:
            return {"message": "Parieur non trouvé"}, 404

        return {"cagnotte": parieur.cagnotte}, 200

    def creer_utilisateur(self, data: dict) -> Utilisateur:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(data['mot_de_passe'].encode('utf-8'), salt)

        utilisateur = Utilisateur(
            email=data['email'],
            mot_de_passe=hashed.decode('utf-8'),
            role=data['role']
        )
        db.session.add(utilisateur)
        db.session.flush()

        if data['role'] == 'parieur':
            parieur = Parieur(utilisateur_id=utilisateur.id)
            db.session.add(parieur)
        elif data['role'] == 'bookmaker':
            bookmaker = Bookmaker(
                utilisateur_id=utilisateur.id,
                numero_employe=data['numero_employe']
            )
            db.session.add(bookmaker)

        return utilisateur

    def traiter_user_updates(self, data: dict) -> bool:
        if data['type'] == 'nouveau_depot':
            parieur = self.get_parieur_by_utilisateur_id(data['utilisateur_id'])
            if parieur:
                parieur.cagnotte += data['montant']
                db.session.commit()
                print(f"Cagnotte mise à jour : {parieur.cagnotte} pour utilisateur {data['utilisateur_id']}")
                return True
            print(f"Parieur introuvable pour utilisateur_id {data['utilisateur_id']}")
        return False

    def update_cagnotte(self, id: int, montant: float) -> tuple[Parieur, str]:
        parieur = self.get_parieur_by_utilisateur_id(id)
        if not parieur:
            return None, 'Parieur non trouvé'

        try:
            parieur.cagnotte += montant
            db.session.commit()
            return parieur, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
