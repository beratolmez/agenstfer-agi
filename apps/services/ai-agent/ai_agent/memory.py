import os
from contextlib import contextmanager
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg

# In a real app, this should come from a secure config/env
DB_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/agi_db")

@contextmanager
def get_checkpointer():
    """Provides a PostgresSaver checkpointer using a context manager."""
    with psycopg.connect(DB_URI) as conn:
        # PostgresSaver.from_conn_string can also be used depending on langgraph version
        # Here we use a live connection.
        checkpointer = PostgresSaver(conn)
        
        # Setup tables if they don't exist
        checkpointer.setup()
        
        yield checkpointer
