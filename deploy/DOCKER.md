# Mandala Health via Docker

## Requisiti
- Docker + docker compose plugin installati (già presenti su urano, ma l'utente `mandala`
  NON è nel gruppo docker per design: i comandi docker vanno eseguiti con l'account di Alessandro)

## Avvio (account Alessandro su urano)
```bash
cd ~/workspace/mandala-health

# 1. crea .env con le credenziali Cronometer
cat > .env <<'EOF'
CRONOMETER_USERNAME=...
CRONOMETER_PASSWORD=...
EOF
chmod 600 .env

# 2. build + up
docker compose up -d --build

# 3. verifica
curl -s http://localhost:8020/api/today | head -c 300
```

Dal telefono (stessa rete): `http://<ip-urano>:8020`

## Persistenza
- SQLite in `./data/` (bind mount) — sopravvive a rebuild/upgrade del container

## Aggiornamento
```bash
git pull && docker compose up -d --build
```

## Nota permessi
`docker` richiede gruppo docker o rootless docker; su urano mandala ha accesso
negato al socket per policy → eseguire con l'account amministratore, oppure
`sudo usermod -aG docker mandala` se si vuole delegare (decisione di Alessandro).
