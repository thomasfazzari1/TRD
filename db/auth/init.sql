-- db/auth/init.sql
CREATE TABLE IF NOT EXISTS utilisateurs (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    mot_de_passe VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('parieur', 'bookmaker', 'admin')),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parieurs (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER UNIQUE NOT NULL REFERENCES utilisateurs(id),
    cagnotte DECIMAL(15,2) DEFAULT 0.00,
    statut VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (statut IN ('actif', 'suspendu', 'bloqué')),
    CONSTRAINT fk_utilisateur
        FOREIGN KEY(utilisateur_id)
        REFERENCES utilisateurs(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bookmakers (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER UNIQUE NOT NULL REFERENCES utilisateurs(id),
    numero_employe VARCHAR(50) UNIQUE NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (statut IN ('actif', 'inactif')),
    CONSTRAINT fk_utilisateur
        FOREIGN KEY(utilisateur_id)
        REFERENCES utilisateurs(id)
        ON DELETE CASCADE
);