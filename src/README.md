# Project Title (WAPlus Dashboard)

## Running with Docker

This application is designed to be run with Docker. The Docker container uses an `entrypoint.sh` script that performs several startup tasks, including:
1.  Waiting for the database to become available.
2.  Applying any pending database migrations using Alembic.
3.  Starting the main application.

### Environment Variables for Database Connection

To ensure the application and migrations can connect to your database, you **must** provide the following environment variables when running the Docker container (e.g., via `docker run -e VAR=value ...` or a `docker-compose.yml` file):

*   `DB_HOST`: The hostname or IP address of your database server (e.g., `localhost`, `postgres_db`).
*   `DB_PORT`: The port number on which your database server is listening (e.g., `5432` for PostgreSQL).
*   `DB_USER`: The username for connecting to the database.
*   `DB_PASSWORD`: The password for the database user.
*   `DB_NAME`: The name of the database to connect to.

**Alternatively, your application or Alembic setup might use a single `DATABASE_URL` connection string:**

*   `DATABASE_URL`: A full database connection string (e.g., `postgresql://user:password@host:port/dbname`). If this is used, ensure it's correctly parsed by `alembic/env.py` and your application's database configuration. The `entrypoint.sh` script's database wait logic currently uses `DB_HOST` and `DB_PORT` directly. If you solely use `DATABASE_URL`, you might need to adjust the wait logic in `entrypoint.sh` or ensure `DB_HOST` and `DB_PORT` are also set for the wait logic to function.

These variables are crucial for:
- The `entrypoint.sh` script to check for database availability before attempting migrations.
- Alembic to connect to the database and apply migrations.
- The application itself to connect to the database during its operation.

Make sure these environment variables are correctly configured in your Docker runtime environment.
