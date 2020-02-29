import os
import traceback
from typing import Tuple

from app.repository import Repository, RepositoryError, VersionTableNotExistsError

def list_migrations(directory: str, extension=".psql", prefix="satnogs-") -> Tuple[int, str]:
    filenames = os.listdir(directory)

    migrations = []

    for filename in filenames:
        if not filename.endswith(extension):
            continue
        if not filename.startswith(prefix):
            continue
        path = os.path.join(directory, filename)
        if not os.path.isfile(path):
            continue

        version_raw, _ = os.path.splitext(filename)
        version_raw = version_raw.lstrip(prefix)
        version = int(version_raw)
        migrations.append((version, path))
    
    migrations.sort(key=lambda p: p[0])
    return migrations

def migrate(config=None, migration_directory="db"):
    repository = Repository(config)

    db_version = repository.get_database_version()

    migrations = list_migrations(migration_directory)

    with repository.transaction() as transaction:
        for migration_version, migration_path in migrations:
            if migration_version <= db_version:
                print("Skip to %d version migration" % (migration_version,))
                continue
        
            print("Process to %d version migration..." % (migration_version,), end="")
            with open(migration_path) as migration_file:
                content = migration_file.read()

            repository.execute_raw_query(content)
            print("OK")

        transaction.commit()

    new_db_version = repository.get_database_version()
    print("Migration complete from %d to %d!" % (db_version, new_db_version))

if __name__ == '__main__':
    migrate()