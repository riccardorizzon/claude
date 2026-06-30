# Cursor CLI Chat — setup personalizzato

Chat CLI efficiente con account Cursor: regole personali, alias shell e installazione guidata.

## Setup rapido (sul tuo Mac/Linux)

```bash
git clone <questo-repo>
cd claude
chmod +x setup/install.sh
./setup/install.sh
source ~/.zshrc   # oppure ~/.bashrc
agent login
```

## Comandi quotidiani

| Comando | Cosa fa |
|---|---|
| `chatnew` | Nuova conversazione ask (solo Q&A, non modifica file) |
| `chat` | Riprende l'ultima chat ask |
| `code` | Agente completo per coding nel progetto corrente |
| `chats` | Elenco sessioni salvate |
| `chatresume` | Riprende l'ultima sessione |

## Personalizzazione

### Regole globali

Modifica `~/.cursor/rules/personal-chat.mdc` dopo l'install, oppure edita il file sorgente in `.cursor/rules/personal-chat.mdc` e rilancia `./setup/install.sh`.

Aggiungi il tuo stack, preferenze di tono e vincoli di lavoro nella sezione "Contesto tecnico".

### Regole per progetto

Crea `.cursor/rules/` dentro un repo specifico per override locali (es. convenzioni del team).

### Config CLI

File: `~/.cursor/cli-config.json` — modello default, vim mode, permessi comandi.

### MCP (opzionale)

File: `~/.cursor/mcp.json` — integra GitHub, Datadog, database, ecc.

## Struttura

```
.cursor/rules/personal-chat.mdc   # Regole personali (sorgente)
setup/install.sh                # Installa CLI, regole, alias
setup/aliases.sh                # Alias shell
setup/cli-config.example.json   # Config CLI di base
```

## Upgrade futuro

Se vuoi una TUI più ricca (pannelli, diff, slash command):

- [OpenCode](https://github.com/anomalyco/opencode) + [cursor-oauth-opencode](https://github.com/jaredboynton/cursor-oauth-opencode)

Le regole in `~/.cursor/rules/` restano valide.
