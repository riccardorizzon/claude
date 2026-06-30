# Cursor CLI — alias per chat personalizzata
# Aggiunto automaticamente da setup/install.sh

# Chat pura (Q&A, nessuna modifica file)
alias chat='agent --mode ask --continue'

# Nuova conversazione ask
alias chatnew='agent --mode ask'

# Agente completo per coding (file, terminal, tool)
alias code='agent --continue'

# Lista sessioni e riprendi l'ultima
alias chats='agent ls'
alias chatresume='agent resume'
