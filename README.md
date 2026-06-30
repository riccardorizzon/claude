# Cursor Mini Chat

Chat web stile Cursor, alimentata dalla CLI `agent` del tuo account Cursor.

## Avvio rapido

```bash
chmod +x start-chat.sh setup/install.sh
./setup/install.sh

# Auth (scegli una)
export CURSOR_API_KEY="key_..."   # da cursor.com/settings
# oppure: agent login

# Avvia chat
./start-chat.sh
```

Apri **http://localhost:8765**

### Demo senza auth (UI + risposte simulate)

```bash
CHAT_USE_MOCK=1 ./start-chat.sh
```

## Comandi utili

| Comando | Descrizione |
|---|---|
| `./start-chat.sh` | Avvia server web chat |
| `curl localhost:8765/api/health` | Stato auth e sessioni |
| `pytest chat/tests -v` | Test automatici |

## Modalità chat

- **Ask** — Q&A read-only (come ChatGPT)
- **Plan** — pianificazione senza modifiche
- **Agent** — coding completo (file, shell, tool)

## Personalizzazione

Regole globali: `.cursor/rules/personal-chat.mdc` (copiate in `~/.cursor/rules/` da `setup/install.sh`)

## Documentazione

- [Piano operativo end-to-end](docs/OPERATIONS.md)
- [Piano implementazione](docs/superpowers/plans/2026-06-30-cursor-chat-webapp.md)

## Struttura

```
chat/app/          Backend FastAPI + wrapper agent CLI
chat/static/       UI chat (HTML/CSS/JS)
chat/data/         Sessioni SQLite (generato)
start-chat.sh      Avvio one-command
setup/             Install CLI, regole, alias shell
```
