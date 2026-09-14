"""Run QA in a disposable PostgreSQL schema, never in public tables."""
import os
import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.config import DATABASE_URL
from sqlalchemy import create_engine, text
schema = 'qa_' + uuid.uuid4().hex
engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 10})
with engine.begin() as connection:
    connection.execute(text(f'CREATE SCHEMA {schema}'))
try:
    from app.database import engine as app_engine, Base
    from sqlalchemy import event
    @event.listens_for(app_engine, 'connect')
    def set_schema(connection, record):
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {schema}')
        connection.commit()
    import app.models
    Base.metadata.create_all(app_engine)
    import pytest
    result = pytest.main(sys.argv[1:] or ['tests/qa/test_regression.py', '-q'])
    app_engine.dispose()
finally:
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
    engine.dispose()
sys.exit(result)
