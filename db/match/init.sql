-- db/match/init.sql
CREATE TABLE IF NOT EXISTS competitions (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    actif BOOLEAN DEFAULT true,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS equipes (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL REFERENCES competitions(id),
    equipe_domicile_id INTEGER NOT NULL REFERENCES equipes(id),
    equipe_exterieur_id INTEGER NOT NULL REFERENCES equipes(id),
    date_match TIMESTAMP NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'à_venir' CHECK (statut IN ('à_venir', 'en_cours', 'terminé')),
    score_domicile INTEGER,
    score_exterieur INTEGER,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cotes (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    cote_domicile DECIMAL(6,2) NOT NULL,
    cote_nul DECIMAL(6,2) NOT NULL,
    cote_exterieur DECIMAL(6,2) NOT NULL,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
