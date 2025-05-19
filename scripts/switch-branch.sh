#!/bin/bash
# filepath: switch-branch.sh

# Verificar si se proporcionó un nombre de rama
if [ -z "$1" ]; then
  echo "Uso: $0 \"nombre-de-la-rama\""
  exit 1
fi

BRANCH_NAME="$1"
REPOS=("backend" "frontend" "indexes" "parser" "tests")

for repo in "${REPOS[@]}"; do
  if [ -d "$repo/.git" ]; then
    echo "Procesando repositorio: $repo"
    cd "$repo"
    
    # Verificar si la rama existe
    if git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
      git checkout $BRANCH_NAME
      echo "✅ Cambiado a rama '$BRANCH_NAME' en $repo"
    else
      echo "⚠️ La rama '$BRANCH_NAME' no existe en $repo"
    fi
    
    cd ..
  else
    echo "⚠️ No se encontró repositorio git en $repo"
  fi
done

echo "Proceso de cambio de ramas completado"