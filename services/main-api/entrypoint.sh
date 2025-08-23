#!/bin/sh

# Inicia la aplicación que se pasa como argumentos (el CMD del Dockerfile) en segundo plano.
"$@" &

# Obtiene el ID del proceso hijo (la aplicación de Python).
child=$!

# Define una función de limpieza que se ejecutará al recibir una señal.
# Pasa la señal SIGTERM al proceso hijo.
_term() {
  echo ">>> Atrapada la señal SIGTERM, enviándola al proceso hijo $child..."
  kill -TERM "$child" 2>/dev/null
}

# Atrapa la señal SIGTERM y llama a la función _term.
trap _term SIGTERM

# Espera a que el proceso hijo termine.
# 'wait' detiene la ejecución del script hasta que el proceso hijo finalice,
# permitiendo que el cierre ordenado se complete.
echo ">>> El entrypoint está esperando al proceso hijo $child..."
wait "$child"
echo ">>> El proceso hijo ha terminado. El entrypoint saldrá ahora."
