# Employee Management System

A learning-focused employee management application built with FastAPI, PostgreSQL, SQLAlchemy 2, Alembic, Pydantic v2, JWT, and a vanilla HTML/CSS/JavaScript frontend. It has separate administrator and employee accounts, and the backend checks authorization on every protected API request.

> **Database:** PostgreSQL is required. The application does not silently fall back to SQLite or create production tables on startup. Apply the Alembic migration before running it.

## Features

- Login, logout, Argon2 password hashes, signed expiring JWTs, and HttpOnly session cookies.
- Admin-only employee and department management, attendance recording, leave reviews, and organization dashboard.
- Employee self-service profile, personal attendance, and leave requests.
- Department, employee, attendance, and leave records stored in PostgreSQL with foreign keys and database constraints.
- Search, status and department filters, and paginated employee listing.
- Duplicate employee code, email, and same-day attendance prevention; overlapping pending or approved leave prevention.
- A responsive interface with loading/error messages and no hardcoded business data.
- Alembic migrations, a secure interactive administrator-creation command, and automated tests that require a dedicated PostgreSQL test database.

## Requirements

- Windows PowerShell.
- Python 3.11 or newer. Python 3.12 is recommended.
- PostgreSQL 14 or newer.

Check your Python installation:

```powershell
py -0p
py -3.12 --version
```

If needed, install Python 3.12 from the official installer or with Windows Package Manager:

```powershell
winget install --id Python.Python.3.12 -e
```

Open a **new** PowerShell window after installing Python.

## 1. Install and configure PostgreSQL

Install PostgreSQL from the official Windows installer or, if available:

```powershell
winget install --id PostgreSQL.PostgreSQL.17 -e
```

Open a new PowerShell window once setup is complete. Check that the PostgreSQL service is running:

```powershell
Get-Service *postgres*
```

## 2. Create the Python environment and install dependencies

In PowerShell:

```powershell
cd "C:\Users\amitk\OneDrive\Desktop\Ai Engineer\employee-management-system"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow it for **this PowerShell process only**, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install the project's dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Set environment variables

Create your local, ignored `.env` file and open it:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set unique, random passwords in the `DATABASE_URL` and `TEST_DATABASE_URL` values. You can generate URL-safe passwords from PowerShell:

```powershell
py -3.12 -c "import secrets; print(secrets.token_hex(24))"
```

Run that command twice and put the different results into the application and test database URLs. The `setup_postgres` command below securely applies those passwords to the PostgreSQL roles. Generate a separate random JWT secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into the `JWT_SECRET_KEY` setting in `.env`; do not put a real secret in `.env.example` or source control. `COOKIE_SECURE=false` is appropriate for local HTTP development. Use HTTPS and set `COOKIE_SECURE=true` when serving the application over HTTPS.

For local use, keep `FRONTEND_ORIGIN=http://127.0.0.1:8000`, which serves the frontend and API from the same FastAPI origin. The application does not accept every CORS origin.

## 4. Create PostgreSQL roles and databases

With `.venv` activated and `.env` configured, run:

```powershell
python -m scripts.setup_postgres
```

Enter your PostgreSQL administrator password when prompted. The command creates separate `ems_app` and `ems_test` roles and databases, applying the passwords in `.env` without printing them. It is safe to run again to resynchronize those role passwords; it doesn't delete database contents. `psql` is not required. If your PostgreSQL administrator has a different name or your server uses another host or port, run `python -m scripts.setup_postgres --help` for options.

## 5. Create the tables with Alembic

```powershell
python -m alembic upgrade head
```

## 6. Create your first administrator account

```powershell
python -m scripts.create_admin --email admin@example.com
```

## 7. Run the application

```powershell
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/login and sign in with the admin account you created.

The Alembic command above applies the initial, versioned PostgreSQL migration. The app does **not** automatically create or reset production tables. The admin-creation command prompts for a password without displaying it; only its Argon2 hash is stored.

Open the following URLs:

- Sign in: http://127.0.0.1:8000/login
- Employee management workspace: http://127.0.0.1:8000/
- Interactive API documentation: http://127.0.0.1:8000/docs
- API health check: http://127.0.0.1:8000/health

Add a department before adding employee accounts. The employee-create form asks the admin to provide a temporary password for that employee.

To stop the development server, press **Ctrl+C** in the server's PowerShell window.

## API overview

All application APIs start with `/api/v1`. Authenticate with the HttpOnly cookie created by the login endpoint or send a bearer access token.

| Area | Endpoints |
|---|---|
| Authentication | `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` |
| Employees | `GET /employees`, `GET /employees/me`, `POST /employees`, `GET /employees/{id}`, `PATCH /employees/{id}`, `DELETE /employees/{id}` |
| Departments | `GET /departments`, `POST /departments`, `PATCH /departments/{id}`, `DELETE /departments/{id}` |
| Attendance | `GET /attendance`, `GET /attendance/summary`, `POST /attendance` |
| Leave | `GET /leave-requests`, `POST /leave-requests`, `PATCH /leave-requests/{id}` |
| Dashboard | `GET /dashboard/stats` |

Employees see only their own employee profile, attendance records, and leave requests. Admin-only operations are checked on the server; hiding a button in the frontend is not treated as authorization.

## Run the tests

Tests create temporary tables **only in the configured test database**, then remove those test tables. They refuse a `TEST_DATABASE_URL` whose database name does not end with `_test` and refuse to use the same database as `DATABASE_URL`. Create the test database and role in the PostgreSQL setup section before running:

```powershell
python -m pytest -v
```

If `TEST_DATABASE_URL` is not set, the security unit tests run while PostgreSQL integration tests are skipped. If PostgreSQL isn't installed or running, the integration tests cannot run; no other database is substituted. Document the actual result in the internship report after running this command on your configured machine.

## Common issues

- **`could not connect to server`**: Start the PostgreSQL Windows service and confirm its host and port. Check `Get-Service *postgres*`.
- **`password authentication failed`**: Check the username, password, database name, and URL encoding in `.env`.
- **`database ... does not exist`**: Connect to PostgreSQL as the admin role and create the application and test databases.
- **`JWT_SECRET_KEY` validation error**: Set a random secret in `.env` with at least 32 characters.
- **Employee form says a department is missing**: Create a department first.
- **Department cannot be deleted**: Reassign or remove its employees first.
- **Leave request overlaps existing dates**: The system deliberately rejects dates overlapping an existing pending or approved request.
- **PowerShell won't activate `.venv`**: Apply `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that PowerShell process only.
- **Port 8000 is in use**: Stop the other local server, or start this app with `python -m uvicorn app.main:app --reload --port 8001`. Update `FRONTEND_ORIGIN` to `http://127.0.0.1:8001` in `.env` if you change the port.

## Project structure

```text
employee-management-system/
├── alembic/                         # Versioned PostgreSQL migrations
│   ├── versions/0001_initial_schema.py
│   └── env.py
├── app/
│   ├── api/v1/                      # HTTP routes and authorization
│   ├── core/                        # Settings, JWT, password hashes, dependencies
│   ├── db/                           # PostgreSQL engine, sessions, declarative base
│   ├── models/                      # SQLAlchemy tables and relationships
│   ├── schemas/                     # Pydantic request/response validation
│   ├── services/                    # Transactional business rules
│   └── main.py                      # FastAPI app and frontend serving
├── docs/project-report-outline.md
├── frontend/                        # Vanilla HTML, CSS, JavaScript
├── scripts/create_admin.py
├── scripts/setup_postgres.py
├── tests/                           # Password/JWT and PostgreSQL API tests
├── .env.example
├── alembic.ini
└── requirements.txt
```

## Architecture in plain language

The browser sends requests to FastAPI. A route validates incoming JSON with a Pydantic schema, gets a short-lived SQLAlchemy session from a dependency, checks who is signed in and whether they may act on the requested record, and calls a service for transactional business rules. Services use the SQLAlchemy models to read or change PostgreSQL rows and return domain errors that the API translates into HTTP responses. Alembic changes the database schema in explicit, reviewable steps. The frontend only displays responses returned by the API; it does not invent employee or dashboard data.

The login response sets an `HttpOnly`, `SameSite=Lax` cookie so ordinary browser JavaScript cannot read the access token. Passwords are hashed with Argon2. The schema stores credentials separately in `users`, and employee profile data refers to the account through a foreign key.
