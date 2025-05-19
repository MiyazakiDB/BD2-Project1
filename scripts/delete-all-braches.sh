#!/bin/bash
# filepath: delete-all-branches.sh

# Verificar si se proporcionó la opción de forzar
FORCE_DELETE=false
if [ "$1" = "--force" ]; then
  FORCE_DELETE=true
fi

# Ramas a preservar (no serán eliminadas)
PROTECTED_BRANCHES=("main" "master" "develop")

REPOS=("backend" "frontend" "indexes" "parser" "tests")

for repo in "${REPOS[@]}"; do
  if [ -d "$repo/.git" ]; then
    echo "Procesando repositorio: $repo"
    cd "$repo"
    
    # Asegurarse de estar en una rama protegida antes de eliminar
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    SAFE_BRANCH=""
    
    # Buscar una rama segura a la cual cambiar
    for branch in "${PROTECTED_BRANCHES[@]}"; do
      if git show-ref --verify --quiet refs/heads/$branch; then
        SAFE_BRANCH=$branch
        break
      fi
    done
    
    if [ -z "$SAFE_BRANCH" ]; then
      echo "⚠️ No se encontró ninguna rama protegida en $repo. Saltando..."
      cd ..
      continue
    fi
    
    # Cambiar a la rama segura si es necesario
    if [[ ! " ${PROTECTED_BRANCHES[@]} " =~ " ${CURRENT_BRANCH} " ]]; then
      echo "Cambiando a la rama $SAFE_BRANCH..."
      git checkout $SAFE_BRANCH
    fi
    
    echo "Eliminando ramas locales en $repo..."
    
    # Obtener todas las ramas locales excepto las protegidas
    LOCAL_BRANCHES=$(git for-each-ref --format='%(refname:short)' refs/heads/ | grep -v -E "$(IFS="|"; echo "${PROTECTED_BRANCHES[*]}")")
    
    # Eliminar ramas locales
    for branch in $LOCAL_BRANCHES; do
      if [ "$FORCE_DELETE" = true ]; then
        git branch -D $branch
        echo "✅ Rama local '$branch' eliminada de $repo (forzado)"
      else
        git branch -d $branch 2>/dev/null
        if [ $? -ne 0 ]; then
          echo "⚠️ La rama '$branch' tiene cambios sin mergear en $repo. Usa --force para forzar eliminación."
        else
          echo "✅ Rama local '$branch' eliminada de $repo"
        fi
      fi
    done
    
    echo "Eliminando ramas remotas en $repo..."
    
    # Obtener todas las ramas remotas excepto las protegidas
    REMOTE_BRANCHES=$(git for-each-ref --format='%(refname:short)' refs/remotes/origin/ | sed 's|origin/||' | grep -v -E "$(IFS="|"; echo "${PROTECTED_BRANCHES[*]}")" | grep -v "HEAD")
    
    # Eliminar ramas remotas
    for branch in $REMOTE_BRANCHES; do
      git push origin --delete $branch
      echo "✅ Rama remota '$branch' eliminada de $repo"
    done
    
    cd ..
  else
    echo "⚠️ No se encontró repositorio git en $repo"
  fi
done

echo "Proceso de eliminación de todas las ramas completado"