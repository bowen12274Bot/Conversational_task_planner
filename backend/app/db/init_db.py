from app.db.base import Base
from app.db.session import engine
from app.db.models import *

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialised successfully.")
    print("Tables created:", list(Base.metadata.tables.keys()))
