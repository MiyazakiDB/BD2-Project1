#!/bin/bash
# filepath: c:\Users\Ian\Desktop\UTEC\CICLO 5\BASE DE DATOS 2\BD2-Proyecto\push-all.sh

REPOS=("backend" "frontend" "indexes" "parser" "tests")

for repo in "${REPOS[@]}"; do
  if [ -d "$repo/.git" ]; then
    echo "Procesando repositorio: $repo"
    cd "$repo"
    
    # Obtener rama actual
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    # Verificar si la rama existe en el remoto
    if git ls-remote --heads origin $CURRENT_BRANCH 2>/dev/null | grep -q .; then
      # Rama existe en remoto, verificar si hay commits para hacer push
      if git log origin/$CURRENT_BRANCH..$CURRENT_BRANCH 2>/dev/null | grep -q .; then
        git push origin $CURRENT_BRANCH
        echo "✅ Push realizado en $repo (rama: $CURRENT_BRANCH)"
      else
        echo "⚠️ No hay cambios para hacer push en $repo"
      fi
    else
      # Rama no existe en remoto, hacer push para crear la rama
      echo "🆕 La rama $CURRENT_BRANCH no existe en el remoto, creándola..."
      git push -u origin $CURRENT_BRANCH
      echo "✅ Rama $CURRENT_BRANCH creada y push realizado en $repo"
    fi
    
    cd ..
  else
    echo "⚠️ No se encontró repositorio git en $repo"
  fi
done

echo "Proceso de push completado"