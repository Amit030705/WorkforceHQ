import argparse
import getpass

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

from app.core.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create or update this application's PostgreSQL roles and databases."
    )
    parser.add_argument("--admin-user", default="postgres", help="PostgreSQL administrator role (default: postgres)")
    parser.add_argument("--host", default="localhost", help="PostgreSQL administrator host (default: localhost)")
    parser.add_argument("--port", type=int, default=5432, help="PostgreSQL administrator port (default: 5432)")
    args = parser.parse_args()

    settings = get_settings()
    if settings.test_database_url is None:
        parser.error("Set TEST_DATABASE_URL in .env before configuring the test database.")

    application = make_url(str(settings.database_url))
    testing = make_url(str(settings.test_database_url))
    if not application.username or not application.password or not application.database:
        parser.error("DATABASE_URL must include an application role, password, and database name.")
    if not testing.username or not testing.password or not testing.database:
        parser.error("TEST_DATABASE_URL must include a test role, password, and database name.")
    if application.username == testing.username or application.database == testing.database:
        parser.error("Use different PostgreSQL roles and databases for the application and tests.")
    if not testing.database.endswith("_test"):
        parser.error("The dedicated test database name must end with _test.")

    admin_password = getpass.getpass("PostgreSQL administrator password (not displayed): ")
    targets = (("application", application), ("test", testing))

    with psycopg.connect(
        host=args.host,
        port=args.port,
        dbname="postgres",
        user=args.admin_user,
        password=admin_password,
        connect_timeout=5,
        autocommit=True,
    ) as connection:
        with connection.cursor() as cursor:
            for label, target in targets:
                cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (target.username,))
                if cursor.fetchone():
                    cursor.execute(
                        sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                            sql.Identifier(target.username),
                            sql.Literal(target.password),
                        )
                    )
                else:
                    cursor.execute(
                        sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
                            sql.Identifier(target.username),
                            sql.Literal(target.password),
                        )
                    )

                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target.database,))
                if cursor.fetchone():
                    cursor.execute(
                        sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                            sql.Identifier(target.database),
                            sql.Identifier(target.username),
                        )
                    )
                else:
                    cursor.execute(
                        sql.SQL("CREATE DATABASE {} OWNER {}").format(
                            sql.Identifier(target.database),
                            sql.Identifier(target.username),
                        )
                    )
                print(f"Configured {label} role and database: {target.username}@{target.database}")

    print("PostgreSQL setup complete. No database contents were deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
