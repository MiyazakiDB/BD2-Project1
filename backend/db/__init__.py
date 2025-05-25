from backend.db.database import Base, engine
import backend.db.models

Base.metadata.create_all(bind=engine)

print(f"Database initialized at: {engine.url}")
