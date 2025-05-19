#!/bin/bash
# filepath: delete-branch.sh

# Verificar si se proporcionó un nombre de rama
if [ -z "$1" ]; then
  echo "Uso: $0 nombre-de-la-rama [--force]"
  echo "Opciones:"
  echo "  --force    Forzar eliminación incluso si la rama tiene cambios sin mergear"
  exit 1
fi

BRANCH_NAME="$1"
FORCE_DELETE=false

# Verificar si se proporcionó la opción de forzar
if [ "$2" = "--force" ]; then
  FORCE_DELETE=true
fi

REPOS=("backend" "frontend" "indexes" "parser" "tests")

for repo in "${REPOS[@]}"; do
  if [ -d "$repo/.git" ]; then
    echo "Procesando repositorio: $repo"
    cd "$repo"
    
    # Asegurarse de no estar en la rama que se va a eliminar
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" = "$BRANCH_NAME" ]; then
      echo "⚠️ Estás en la rama que intentas eliminar. Cambiando a main/master..."
      if git rev-parse --verify --quiet main >/dev/null; then
        git checkout main
      else
        git checkout master
      fi
    fi
    
    # Verificar si la rama existe localmente
    if git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
      # Eliminar rama local
      if [ "$FORCE_DELETE" = true ]; then
        git branch -D $BRANCH_NAME
      else
        git branch -d $BRANCH_NAME 2>/dev/null
        if [ $? -ne 0 ]; then
          echo "⚠️ La rama '$BRANCH_NAME' tiene cambios sin mergear en $repo. Usa --force para forzar eliminación."
          cd ..
          continue
        fi
      fi
      echo "✅ Rama local '$BRANCH_NAME' eliminada de $repo"
    else
      echo "⚠️ La rama local '$BRANCH_NAME' no existe en $repo"
    fi
    
    # Verificar si la rama existe en remoto
    if git ls-remote --heads origin $BRANCH_NAME 2>/dev/null | grep -q .; then
      # Eliminar rama remota
      git push origin --delete $BRANCH_NAME
      echo "✅ Rama remota '$BRANCH_NAME' eliminada de $repo"
    else
      echo "⚠️ La rama remota '$BRANCH_NAME' no existe en $repo"
    fi
    
    cd ..
  else
    echo "⚠️ No se encontró repositorio git en $repo"
  fi
done

echo "Proceso de eliminación de rama completado"