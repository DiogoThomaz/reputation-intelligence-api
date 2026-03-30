from app.db.session import Base, engine


def init_db() -> None:
    # Import models to register metadata
    from app.domain import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
