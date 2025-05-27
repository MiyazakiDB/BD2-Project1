# BD2-Proyecto

Este proyecto contiene múltiples repositorios que trabajan en conjunto para implementar una solución completa.

## 📂 Estructura del Proyecto

- `backend`: Contiene la lógica del servidor y las APIs
- `frontend`: Contiene la interfaz de usuario
- `indexes`: Contiene los índices para optimización
- `parser`: Contiene el analizador de datos
- `tests`: Contiene las pruebas unitarias y de integración

## 🛠️ Scripts de Utilidad

Esta sección describe los scripts de utilidad disponibles para facilitar el manejo del proyecto en todos sus repositorios.

### Scripts de Commit y Push

#### 📤 commit-all.sh

Este script realiza commits en todos los repositorios del proyecto con el mismo mensaje.

```bash
./commit-all.sh "mensaje de commit"
```

**Características:**
- Añade automáticamente todos los archivos modificados (`git add .`)
- Aplica el mismo mensaje de commit a todos los repositorios
- Verifica si hay cambios antes de intentar realizar el commit
- Reporta el estado de cada repositorio

#### 📤 push-all.sh

Este script envía (push) los cambios de todos los repositorios a sus respectivos remotos.

```bash
./push-all.sh
```

**Características:**
- Detecta automáticamente la rama actual en cada repositorio
- Verifica si la rama existe en el remoto y la crea si es necesario
- Verifica si hay commits pendientes de push antes de intentar enviarlos
- Proporciona información detallada sobre el proceso en cada repositorio

### Scripts de Gestión de Ramas

#### 🔄 pull-all.sh

```bash
./pull-all.sh nombre-de-la-rama [--checkout]
```

**Opciones:**
- `nombre-de-la-rama`: Nombre de la rama de la cual hacer pull (requerido)
- `--checkout`: (Opcional) Cambia automáticamente a la rama especificada antes de realizar el pull

**Comportamiento:**
- Si se usa `--checkout`, cambiará a la rama especificada antes de hacer pull
- Si la rama no existe localmente pero existe en remoto, la creará
- Si estás en otra rama y no usas `--checkout`, solo actualizará las referencias remotas

#### 🔀 switch-branch.sh

```bash
./switch-branch.sh "nombre-de-la-rama"
```

**Características:**
- Cambia a la rama especificada en todos los repositorios 
- Verifica si la rama existe antes de intentar cambiar a ella
- Reporta el estado del proceso para cada repositorio

#### 🌱 create-branch.sh

```bash
./create-branch.sh "nombre-de-la-rama"
```

**Características:**
- Crea una nueva rama con el nombre especificado en todos los repositorios
- Automáticamente cambia a la rama recién creada
- Útil para iniciar nuevas características que afectan a múltiples componentes

#### ✂️ delete-branch.sh

```bash
./delete-branch.sh nombre-de-la-rama [--force]
```

**Opciones:**
- `nombre-de-la-rama`: Nombre de la rama a eliminar
- `--force`: (Opcional) Forzar eliminación incluso si la rama tiene cambios sin mergear

**Comportamiento:**
- Cambia automáticamente a una rama segura antes de eliminar
- Elimina la rama tanto local como remotamente
- Previene errores verificando si hay cambios no mergeados

#### 🗑️ delete-all-branches.sh

```bash
./delete-all-braches.sh [--force]
```

**Opciones:**
- `--force`: (Opcional) Forzar eliminación incluso si las ramas tienen cambios sin mergear

**Características:**
- Preserva automáticamente las ramas protegidas (main, master, develop)
- Elimina todas las demás ramas tanto local como remotamente
- Útil para limpieza masiva de ramas después de un sprint o release

### Ventajas de usar estos scripts

1. **Consistencia**: Asegura que todas las operaciones se apliquen uniformemente a todos los repositorios
2. **Eficiencia**: Reduce significativamente el tiempo necesario para administrar múltiples repositorios
3. **Prevención de errores**: Incluye verificaciones y validaciones que previenen errores comunes
4. **Colaboración mejorada**: Facilita el trabajo en equipo al simplificar la sincronización

## 📅 Cronograma General

| Día | Actividades Principales                                                                 |
|-----|------------------------------------------------------------------------------------------|
| 1–6 | Implementación de estructuras de indexación (AVL, ISAM, Hash, B+, R-Tree)               |
| 7–10| Parser SQL personalizado + backend API (Flask o FastAPI)                                |
| 11–13| Desarrollo del frontend (GUI para ejecutar consultas y mostrar resultados)             |
| 14–16| Pruebas de rendimiento (tiempo y accesos a disco), análisis comparativo                |
| 17–18| Documentación final + grabación del video explicativo (máx. 15 min)                    |
| 19   | Revisión completa del sistema (end-to-end), verificación de entregables                |
| 20   | Entrega final (subir enlace del repositorio a Canvas, compartir video y documentación) |

## ✅ Entregables Finales

- Código en GitHub (organizado y documentado)
- Informe técnico (Markdown o PDF)
- Comparativa de índices (gráficas + análisis)
- Interfaz gráfica funcional
- Video explicativo con participación de todo el grupo
- Enlace público del repositorio en Canvas

---
