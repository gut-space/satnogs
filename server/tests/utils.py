import psycopg2
from migrate_db import migrate

def standard_seed_db(postgresql):
    config = postgresql.dsn()
    migrate(config)

    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cursor:
            with open("tests/db-data.psql", "rt") as f:
                cursor.execute(f.read())
                conn.commit()
