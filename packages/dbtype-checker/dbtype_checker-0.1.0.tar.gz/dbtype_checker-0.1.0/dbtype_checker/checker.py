from .db import connect, get_table_names, fetch_table_data, close_connection
from .utils import infer_type

def check_column_types(db_url):
    engine, session = connect(db_url)
    tables = get_table_names(engine)

    mismatches = []

    for table in tables:
        records = fetch_table_data(session, table)
        if not records:
            continue

        sample = records[0]
        for key, val in sample.items():
            expected = infer_type(key)
            if val is not None and not isinstance(val, expected):
                mismatches.append((table, key, type(val).__name__, expected.__name__))

    close_connection(session)
    return mismatches
