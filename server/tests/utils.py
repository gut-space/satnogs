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


def check_output(output: str, strings):
    """Checks if specified output (presumably stdout) has appropriate content. strings
    is a list of strings that are expected to be present. They're expected
    to appear in the specified order, but there may be other things
    printed in between them. Will assert if string is not found. """
    offset = 0
    for s in strings:
        new_offset = output.find(s, offset)

        if (new_offset == -1):
            assert False, "Not found an expected string: '%s'" % s
        # string found, move to its end and continue searching
        offset = new_offset + len(s)
