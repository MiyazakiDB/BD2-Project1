# BD2-Proyecto

Este proyecto contiene múltiples repositorios que trabajan en conjunto para implementar una solución completa.

## 📂 Estructura del Proyecto

- `backend`: Contiene la lógica del servidor y las APIs
- `frontend`: Contiene la interfaz de usuario
- `indexes`: Contiene los índices para optimización
- `parser`: Contiene el analizador de datos
- `tests`: Contiene las pruebas unitarias y de integración

## 🛠️ Scripts de Utilidad

Esta sección describe los scripts de utilidad disponibles para facilitar el manejo del proyecto.

### Pull-All Script

El script `pull-all.sh` permite actualizar todos los repositorios del proyecto desde una rama específica de manera simultánea.

#### Uso

```bash
./pull-all.sh nombre-de-la-rama [--checkout]
```

#### Opciones

- `nombre-de-la-rama`: Nombre de la rama de la cual hacer pull (requerido)
- `--checkout`: (Opcional) Cambia automáticamente a la rama especificada antes de realizar el pull

#### Repositorios Afectados

El script opera sobre los siguientes repositorios:
- `backend`
- `frontend`
- `indexes`
- `parser`
- `tests`

#### Comportamiento

1. Si se usa `--checkout`, el script cambiará a la rama especificada antes de hacer pull
2. Si la rama no existe localmente pero existe en remoto, la creará
3. Si estás en otra rama y no usas `--checkout`, solo actualizará las referencias remotas
4. Proporciona mensajes claros sobre el estado del proceso para cada repositorio
