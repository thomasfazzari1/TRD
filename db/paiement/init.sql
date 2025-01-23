-- db/paiement/init.sql
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    type_transaction VARCHAR(20) NOT NULL CHECK (type_transaction IN ('dépôt', 'retrait', 'gain', 'mise')),
    montant DECIMAL(15,2) NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'en_cours' CHECK (statut IN ('en_cours', 'validé', 'refusé')),
    reference VARCHAR(100) UNIQUE NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);