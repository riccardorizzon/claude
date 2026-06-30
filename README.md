# Cursor — Agente personale

Questa repo è la **base per le chat Cursor**: ogni nuova conversazione eredita automaticamente le tue preferenze.

## Uso (30 secondi)

1. Apri Cursor su questa repo
2. **Nuova chat** o **Cloud Agent** → l'agente personale è già attivo
3. Scrivi e lavora — tono, lingua e regole sono già configurati

## Dove personalizzare

| File | Cosa controlla |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Identità e regole dell'agente (sempre attive) |
| [`.cursor/rules/personal-chat.mdc`](.cursor/rules/personal-chat.mdc) | Stile, comportamento, stack |

Modifica questi file, fai commit — ogni nuova chat userà la versione aggiornata.

---

## Setup opzionale (CLI / web app)

Il resto del repo include anche setup CLI e mini chat web (non necessari se usi solo Cursor chat):

```bash
chmod +x setup/install.sh
./setup/install.sh
```

Vedi [`docs/OPERATIONS.md`](docs/OPERATIONS.md) per la web app locale.

---

## Struttura

```
chat/app/          Backend FastAPI + wrapper agent CLI
chat/static/       UI chat (HTML/CSS/JS)
chat/data/         Sessioni SQLite (generato)
start-chat.sh      Avvio one-command
setup/             Install CLI, regole, alias shell
```
