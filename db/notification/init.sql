-- db/notification/init.sql
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    titre VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type_notification VARCHAR(50) NOT NULL,
    lu BOOLEAN DEFAULT FALSE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);