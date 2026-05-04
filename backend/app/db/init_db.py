from .base import Base
from .session import engine
from . import models  # noqa: F401 – registers all models with Base.metadata


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("✅ Database initialised successfully.")
    print("   Tables created:", list(Base.metadata.tables.keys()))
