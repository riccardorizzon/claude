#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURSOR_RULES_DIR="${HOME}/.cursor/rules"
SHELL_RC=""

detect_shell_rc() {
  if [[ -n "${ZSH_VERSION:-}" ]] || [[ "${SHELL:-}" == *zsh* ]]; then
    SHELL_RC="${HOME}/.zshrc"
  else
    SHELL_RC="${HOME}/.bashrc"
  fi
}

install_cursor_cli() {
  if command -v agent >/dev/null 2>&1; then
    echo "✓ Cursor CLI (agent) già installato: $(command -v agent)"
    return 0
  fi

  echo "→ Installazione Cursor CLI..."
  curl -fsSL https://cursor.com/install | bash

  if command -v agent >/dev/null 2>&1; then
    echo "✓ Cursor CLI installato"
  else
    echo "! Installazione completata. Aggiungi ~/.local/bin al PATH se agent non è trovato:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi
}

install_rules() {
  mkdir -p "${CURSOR_RULES_DIR}"
  cp "${REPO_ROOT}/.cursor/rules/personal-chat.mdc" "${CURSOR_RULES_DIR}/personal-chat.mdc"
  echo "✓ Regole copiate in ${CURSOR_RULES_DIR}/personal-chat.mdc"
}

install_aliases() {
  detect_shell_rc
  local marker="# cursor-cli-chat-aliases"
  local aliases_file="${REPO_ROOT}/setup/aliases.sh"

  if grep -qF "${marker}" "${SHELL_RC}" 2>/dev/null; then
    echo "✓ Alias già presenti in ${SHELL_RC}"
    return 0
  fi

  {
    echo ""
    echo "${marker}"
    echo "# Cursor CLI chat personalizzata — $(date +%Y-%m-%d)"
    cat "${aliases_file}"
  } >> "${SHELL_RC}"

  echo "✓ Alias aggiunti a ${SHELL_RC}"
  echo "  Esegui: source ${SHELL_RC}"
}

install_cli_config() {
  local config_dir="${HOME}/.cursor"
  local config_file="${config_dir}/cli-config.json"
  local example="${REPO_ROOT}/setup/cli-config.example.json"

  mkdir -p "${config_dir}"

  if [[ -f "${config_file}" ]]; then
    echo "✓ ${config_file} già esistente (non sovrascritto)"
    return 0
  fi

  cp "${example}" "${config_file}"
  echo "✓ Creato ${config_file} (modifica modello default se vuoi)"
}

main() {
  echo "=== Setup Cursor CLI Chat ==="
  echo ""

  install_cursor_cli
  echo ""
  install_rules
  install_aliases
  install_cli_config
  echo ""

  if command -v agent >/dev/null 2>&1 && ! agent status >/dev/null 2>&1; then
    echo "→ Autenticazione richiesta. Esegui:"
    echo "  agent login"
    echo ""
  fi

  echo "=== Comandi disponibili ==="
  echo "  chatnew     Nuova chat (solo Q&A)"
  echo "  chat        Continua l'ultima chat ask"
  echo "  code        Agente coding nel progetto"
  echo "  chats       Lista sessioni"
  echo "  chatresume  Riprendi ultima sessione"
  echo ""
  echo "Prima volta: source ${SHELL_RC:-~/.bashrc} && agent login"
}

main "$@"
