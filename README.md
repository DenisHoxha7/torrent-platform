# torrent-platform
# Piattaforma Torrent (Verifica 5E)

Piattaforma web per la condivisione di file torrent, con:
- Backend REST in Flask
- Database a documenti MongoDB
- Frontend Single Page Application (HTML + JavaScript)
- Gestione utenti con ruoli (user, moderator, admin)
- Commenti, valutazioni e statistiche

## Struttura del progetto

- `backend/`: server API REST (Flask)
- `frontend/`: SPA (HTML, JS, CSS)
- `schema/`: JSON Schema per le collection MongoDB
- `README.md`: documentazione

## Requisiti

- Python 3
- MongoDB in esecuzione (es. su localhost:27017)
- MongoDB Compass per configurare gli schema

## Configurazione Database

1. Apri MongoDB Compass e crea il database `torrent_platform`.
2. Crea le collection:
   - `users`
   - `torrents`
   - `comments`
   - `downloads`
3. In ogni collection imposta il **validator** usando i file in `schema/`.

## Avvio Backend

```bash
cd backend
python app.py
