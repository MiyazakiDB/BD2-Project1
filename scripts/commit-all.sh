#!/bin/bash
# filepath: commit-all.sh

# Verificar si se proporcionó un mensaje de commit
if [ -z "$1" ]; then
  echo "Uso: $0 \"mensaje de commit\""
  exit 1
fi

COMMIT_MESSAGE="$1"
REPOS=("backend" "frontend" "indexes" "parser" "tests")

for repo in "${REPOS[@]}"; do
  if [ -d "$repo/.git" ]; then
    echo "Procesando repositorio: $repo"
    cd "$repo"
    
    # Verificar si hay cambios para commit
    if [ -n "$(git status --porcelain)" ]; then
      git add .
      git commit -m "$COMMIT_MESSAGE"
      echo "✅ Commit realizado en $repo"
    else
      echo "⚠️ No hay cambios en $repo"
    fi
    
    cd ..
  else
    echo "⚠️ No se encontró repositorio git en $repo"
  fi
done

echo "Proceso de commit completado"