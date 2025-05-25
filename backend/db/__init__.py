from backend.db.database import Base, engine
import backend.db.models
from backend.db.models import User, File  # Importar explícitamente para asegurar que se cree

Base.metadata.create_all(bind=engine)

print(f"Base de datos inicializada en: {engine.url}")
