<<<<<<< HEAD
from .base import Base
from .session import engine
from . import models  # noqa: F401 – registers all models with Base.metadata
=======
from app.db.base import Base
from app.db.session import engine
>>>>>>> origin/main


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
<<<<<<< HEAD
    print("✅ Database initialised successfully.")
    print("   Tables created:", list(Base.metadata.tables.keys()))
=======
>>>>>>> origin/main
