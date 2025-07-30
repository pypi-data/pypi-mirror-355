from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

def connect(db_url):
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return engine, Session()

def get_table_names(engine):
    inspector = inspect(engine)
    return inspector.get_table_names()

def fetch_table_data(session, table_name):
    result = session.execute(text(f"SELECT * FROM {table_name} LIMIT 1"))
    return result.mappings().all()

def close_connection(session):
    session.close()
