#!/bin/bash
# filepath: create-branch.sh

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
    
    # Crear rama
    git checkout -b $BRANCH_NAME
    echo "✅ Rama '$BRANCH_NAME' creada en $repo"
    
    cd ..
  else
    echo "⚠️ No se encontró repositorio git en $repo"
  fi
done

echo "Proceso de creación de ramas completado"