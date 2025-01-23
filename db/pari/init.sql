-- db/pari/init.sql
CREATE TABLE IF NOT EXISTS paris_groupes (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    montant DECIMAL(15,2) NOT NULL,
    gain_potentiel DECIMAL(15,2) NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'en_attente' CHECK (statut IN ('en_attente', 'gagné', 'perdu', 'annulé')),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS paris (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    type_pari VARCHAR(20) NOT NULL CHECK (type_pari IN ('domicile', 'nul', 'exterieur')),
    montant DECIMAL(15,2) NOT NULL,
    cote DECIMAL(6,2) NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'en_attente' CHECK (statut IN ('en_attente', 'gagné', 'perdu', 'annulé')),
    gain_potentiel DECIMAL(15,2) NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    groupe_id INTEGER REFERENCES paris_groupes(id),
    annule BOOLEAN DEFAULT FALSE,
    motif_annulation VARCHAR(200)
);