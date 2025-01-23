-- db/panier/init.sql
CREATE TABLE IF NOT EXISTS panier_paris (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    type_pari VARCHAR(20) NOT NULL,
    mise_totale FLOAT NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'en_cours' CHECK (statut IN ('en_cours', 'validé', 'annulé')),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS panier_paris_details (
    id SERIAL PRIMARY KEY,
    panier_id INTEGER REFERENCES panier_paris(id),
    match_id INTEGER NOT NULL,
    pronostic VARCHAR(20) NOT NULL,
    cote FLOAT NOT NULL
);
