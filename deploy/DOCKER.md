# Mandala Health via Docker

## Requisiti
- Docker + docker compose plugin installati (già presenti su urano, ma l'utente `mandala`
  NON è nel gruppo docker per design: i comandi docker vanno eseguiti con l'account di Alessandro)

## Avvio (account Alessandro su urano)
```bash
cd ~/workspace/mandala-health

# 1. build + up (nessuna credenziale necessaria: gli alimenti vengono da Open Food Facts,
#    il diario è locale in ./data)
docker compose up -d --build

# 2. verifica (ricerca alimenti via Open Food Facts)
curl -s "http://localhost:8020/api/foods/search?q=banana" | head -c 300
```

Dal telefono (stessa rete): `http://<ip-urano>:8020`

## Persistenza
- SQLite in `./data/` (bind mount) — sopravvive a rebuild/upgrade del container

## Auto-aggiornamento (watchtower)

`docker-compose.yml` include un servizio **watchtower** che ogni 5 minuti
controlla se su ghcr.io è stata pubblicata un'immagine più recente (cosa che
la CI fa automaticamente a ogni merge su main) e ricrea il container.

Permessi necessari: watchtower usa il socket docker — va eseguito con un
account nel gruppo `docker` (o rootless docker configurato).

Comandi utili:
```bash
docker compose logs watchtower        # vedere i controlli
docker compose exec health curl -s localhost:8020/api/today | head -c 200
```

## Avvio manuale (senza watchtower)

```bash
docker compose up -d health
```

## Nota permessi
`docker` richiede gruppo docker o rootless docker; su urano mandala ha accesso
negato al socket per policy → eseguire con l'account amministratore, oppure
`sudo usermod -aG docker mandala` se si vuole delegare (decisione di Alessandro).
