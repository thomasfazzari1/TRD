from models import db, Transaction
import uuid
from datetime import datetime


class TransactionRepository:
    def create_transaction(self, data: dict, type_transaction: str) -> Transaction:
        transaction = Transaction(
            utilisateur_id=data['utilisateur_id'],
            type_transaction=type_transaction,
            montant=data['montant'],
            reference=f"{type_transaction[:3].upper()}-{uuid.uuid4().hex[:8]}",
            statut=data.get('statut', 'en_attente')
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def get_transactions_by_user(self, utilisateur_id: int) -> list[Transaction]:
        return Transaction.query.filter_by(utilisateur_id=utilisateur_id).all()

    def get_transaction_by_id(self, id: int) -> Transaction:
        return Transaction.query.get(id)