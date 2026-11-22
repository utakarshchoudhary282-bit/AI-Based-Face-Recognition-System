"""Database tables (SQLite through SQLAlchemy)."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from .config import settings

engine = create_engine(settings.DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def now_utc():
    return datetime.now(timezone.utc)


class User(Base):
    """People who sign in to the portal (admin or security guard)."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default="security")          # admin | security


class Employee(Base):
    """A person the face model can recognise. `label` = their photo folder name."""
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    label = Column(String(50), unique=True, nullable=False)
    employee_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), default="")
    designation = Column(String(100), default="")
    access_level = Column(String(10), default="L1")         # L1 .. L4
    email = Column(String(120), default="")
    phone = Column(String(20), default="")
    office_location = Column(String(100), default="")
    shift = Column(String(50), default="General (9:30-18:30)")
    manager = Column(String(100), default="")
    joining_date = Column(String(20), default="")
    status = Column(String(20), default="Active")           # Active | On Leave | Suspended | Exited
    notes = Column(Text, default="")
    photo_path = Column(String(300), default="")


class VerificationLog(Base):
    """One row per photo checked on the Verify page."""
    __tablename__ = "verification_logs"
    id = Column(Integer, primary_key=True)
    checked_by = Column(String(50))
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    predicted_label = Column(String(50), default="")
    similarity = Column(Float, default=0.0)
    result = Column(String(20), default="")                 # MATCH | UNKNOWN | NO_FACE
    created_at = Column(DateTime(timezone=True), default=now_utc)
    employee = relationship("Employee")


def init_db():
    # A database left by an older version may have tables with different columns. Drop those tables
    # (only their rows are lost) so they are recreated with the current columns.
    from sqlalchemy import inspect
    existing = inspect(engine)
    for table in reversed(Base.metadata.sorted_tables):
        if existing.has_table(table.name):
            have = {c["name"] for c in existing.get_columns(table.name)}
            if not {c.name for c in table.columns} <= have:
                table.drop(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
