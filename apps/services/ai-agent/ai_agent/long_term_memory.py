import os
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# We use the same DB as the checkpointer
DB_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/agi_db")

Base = declarative_base()

class UserFact(Base):
    __tablename__ = 'long_term_facts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    fact = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

engine = create_engine(DB_URI.replace("postgresql://", "postgresql+psycopg://"))
SessionLocal = sessionmaker(bind=engine)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass


def save_fact(user_id: str, fact: str):
    """Save an extracted fact to long-term memory."""
    try:
        with SessionLocal() as session:
            new_fact = UserFact(user_id=user_id, fact=fact)
            session.add(new_fact)
            session.commit()
    except Exception:
        pass


def get_facts(user_id: str):
    """Retrieve all facts for a user."""
    try:
        init_db()
        with SessionLocal() as session:
            facts = session.query(UserFact).filter(UserFact.user_id == user_id).all()
            return [f.fact for f in facts]
    except Exception:
        return []
