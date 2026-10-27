# Employee Management System — Internship Report Draft

> Replace every bracketed student, college, organization, supervisor, and duration placeholder with verified details. The test-results section is intentionally blank until tests have actually been run against PostgreSQL.

## Cover page

- **Project title:** Employee Management System
- **Student name:** [Your name]
- **Enrollment number:** [Your enrollment number]
- **College / university:** [Your college and university]
- **Internship organization:** [Organization name]
- **Project supervisor:** [Supervisor name and designation]
- **Internship duration:** [Start date] to [End date]
- **Submission date:** [Date]

## Abstract

This project is a web-based Employee Management System for maintaining employee profiles, departments, attendance, and leave requests. It uses a FastAPI REST API, PostgreSQL as its data store, SQLAlchemy for database access, Alembic for schema changes, and a responsive HTML/CSS/JavaScript interface. Pydantic validates API inputs; administrator and employee accounts have different permissions. Administrators manage organization records, while employees can view their own profile and records and submit leave requests. This report describes the implemented design, security controls, setup, and verification. Actual test outcomes and student/internship details must be recorded after they are verified.

## 1. Introduction and problem statement

Employee details and routine staff processes are often kept in separate documents or handled manually. This makes it harder to keep employee information consistent, track daily attendance, review leave requests, and restrict personal records to the appropriate people.

The project demonstrates a small centralized web application with a relational database, input validation, role-based APIs, and a browser interface. It is an educational prototype, not a claim of production readiness or a substitute for a company's HR, payroll, legal, or privacy review.

## 2. Objectives and scope

### Objectives

1. Store employee and department information in PostgreSQL.
2. Provide API-backed employee, department, attendance, and leave workflows.
3. Authenticate administrators and employees with securely hashed passwords and expiring signed tokens.
4. Enforce admin permissions and employee object-level access in the backend.
5. Show database-backed dashboard counts.
6. Use migrations and automated tests to make changes and verification reproducible.

### Project scope

The implementation includes administrator provisioning, login/logout, employee CRUD and search filters, department CRUD, attendance entries and summaries, leave submission and review, and a responsive browser interface. Integration tests need an explicitly configured, disposable PostgreSQL database.

### Out of scope

This version does not implement payroll processing, email or SMS notifications, multi-factor authentication, employee document uploads, a password-reset service, an enterprise identity provider, time-clock/device integration, a deployment pipeline, or jurisdiction-specific HR rules.

## 3. Requirements

### Functional requirements

- Authenticate administrators and employees and provide logout.
- Restrict user-management operations to administrators.
- Allow an employee to read only their own profile, attendance, and leave requests.
- Create, edit, search, filter, paginate, and delete employee records.
- Manage departments and prevent deletion while employees still belong to them.
- Record one attendance status per employee per date and calculate summaries.
- Submit, list, approve, and reject leave requests with reviewer and review-time details.
- Reject invalid date ranges and overlapping pending or approved requests.
- Calculate dashboard statistics from PostgreSQL records.

### Non-functional requirements

- Keep password hashes, token secrets, and database passwords out of source control.
- Use parameterized SQL through SQLAlchemy and validate request bodies.
- Use PostgreSQL constraints and foreign keys to protect important data invariants.
- Keep routes, validation schemas, persistence models, and user interface code in distinct areas.
- Use versioned Alembic migrations instead of implicit production schema creation.
- Support a dedicated PostgreSQL test database.

## 4. Technology stack and justification

| Technology | Role in this project |
|---|---|
| Python 3.11+ | Backend language |
| FastAPI | Typed REST endpoints, dependency injection, and interactive OpenAPI docs |
| PostgreSQL | Relational data, constraints, indexes, and transactions |
| SQLAlchemy 2.x | ORM models, queries, and session management |
| Alembic | Versioned and reviewable database migrations |
| Pydantic v2 / pydantic-settings | Request/response validation and environment configuration |
| PyJWT | Signed JWT creation and verification with expiration |
| pwdlib with Argon2 | Maintained one-way password hashing |
| HTML, CSS, vanilla JavaScript | Lightweight browser interface without React or Tailwind |
| Pytest and HTTPX | Unit and HTTP/API integration tests |

## 5. System architecture

```text
Browser (HTML/CSS/JavaScript)
          │ HTTP + JSON; HttpOnly session cookie or bearer token
          ▼
FastAPI route (app/api/v1)
          │ Pydantic validation; current-user and role dependencies
          ▼
SQLAlchemy session (app/db)
          │ ORM statements / transactions
          ▼
PostgreSQL database

Alembic ── versioned schema migrations ──► PostgreSQL
```

The browser is served from the same FastAPI origin in local development. Route functions use short-lived database sessions injected by dependencies. The application deliberately does not create or reset the production schema at server startup.

## 6. Database schema and relationships

| Table | Purpose and key relationships |
|---|---|
| `users` | Login email, Argon2 password hash, role, active flag, and timestamps. One employee profile may be linked to a user. |
| `departments` | Unique department name, description, and timestamps. A department can have many employees. |
| `employees` | Unique employee code, email, user link, department foreign key, contact and job details, joining date, salary, employment status, and timestamps. |
| `attendance` | Employee, calendar date, status, optional notes, and recording administrator. Employee and date have a unique constraint. |
| `leave_requests` | Employee, date range, reason, review status, optional reviewer, review time/comment, and timestamps. |

Relationships: a department has many employees; a user can be linked to one employee; an employee has many attendance records and leave requests; attendance records refer to their recording user; a leave request optionally records its reviewing user. Foreign keys, unique constraints, checks, and indexes are represented in the initial Alembic migration.

## 7. API design

API endpoints use the `/api/v1` prefix. FastAPI publishes the OpenAPI interface at `/docs`.

| Resource | Main operations |
|---|---|
| Authentication | Login, logout, current user |
| Employees | List/search/filter/page, current employee profile, create, read, update, delete |
| Departments | List, create, update, delete |
| Attendance | List by employee/date range, daily summary, create |
| Leave requests | Employee submit/list, admin review, status filtering |
| Dashboard | Database-backed organization summary |

The API uses standard status codes, including `201` for creation, `204` for deletion, `401` for missing/invalid authentication, `403` for insufficient permissions, `404` for missing records, `409` for conflicts, and `422` for validation failures. Pydantic response schemas constrain returned data.

## 8. Module-wise implementation

- `app/core/config.py` loads and validates settings without embedding secrets in source.
- `app/core/security.py` hashes/verifies passwords and creates/verifies expiring JWTs.
- `app/core/dependencies.py` authenticates API requests and enforces administrator access.
- `app/db/session.py` provides one database session per request and rolls back failed work.
- `app/models/` defines SQLAlchemy entities, constraints, and relationships.
- `app/schemas/` defines incoming and outgoing Pydantic shapes.
- `app/api/v1/` implements auth, employee, department, attendance, leave, and dashboard routes.
- `app/services/` contains transactional business rules and maps domain conditions to service errors.
- `alembic/` contains the initial PostgreSQL schema migration.
- `scripts/create_admin.py` provisions an admin through a hidden password prompt; `scripts/setup_postgres.py` provisions the PostgreSQL application/test roles and databases.
- `frontend/` contains browser pages, responsive styles, and JavaScript API clients.
- `tests/` contains security and PostgreSQL-backed endpoint tests.

## 9. Authentication and security

Passwords are never stored in plaintext: the admin-provisioning tool and employee creation workflow store Argon2 hashes. Signed JWTs include a subject, role, and expiry and are validated using a configured secret and one supported algorithm. The browser receives an HttpOnly, `SameSite=Lax` session cookie; applications served over HTTPS should enable the secure-cookie setting.

Protected endpoints load the current user from the database. Role claims are checked against the current account role, and employees' accessible employee IDs are taken from their own account relationship rather than trusted from user-supplied filters. Administrator-only APIs have backend dependencies. CORS permits only the configured frontend origin. Database values are supplied through environment settings, ORM operations use bound parameters, and sensitive credentials are excluded from example configuration.

This educational implementation still needs operational security work before any real HR deployment. See limitations below.

## 10. Testing methodology and actual results

The test suite includes tests for password hashing, JWT claims and expiry, login failures, account permissions, employee CRUD and uniqueness, department deletion rules, duplicate daily attendance, leave submission/overlap/review, own-record access, and dashboard counts.

API integration tests require a dedicated PostgreSQL database named with a `_test` suffix. They create temporary test tables and remove those tables afterward; they reject a test URL pointing to the configured application database. No substitute database is used.

**Actual test execution record — fill this in after running `python -m pytest -v`:**

- Execution date: [Date]
- Command: `python -m pytest -v`
- Python version: [Observed version]
- PostgreSQL version / test database: [Observed version and dedicated database name, omit credentials]
- Passed: [Actual count]
- Failed: [Actual count]
- Skipped: [Actual count and reasons]
- Failure notes / remediation: [Actual output summary, or “None” only if confirmed]

No test count or successful run is asserted in this draft.

## 11. Setup and deployment instructions

Follow the repository `README.md` for exact Windows PowerShell commands. In summary:

1. Install Python 3.11+ and PostgreSQL.
2. Create separate application and test roles/databases.
3. Create and activate a Python virtual environment.
4. Install `requirements.txt`.
5. Copy `.env.example` to `.env`, configure PostgreSQL URLs, generate a random JWT secret, and configure the frontend origin.
6. Apply `python -m alembic upgrade head`.
7. Create the first administrator using `python -m scripts.create_admin --email ...`.
8. Start `python -m uvicorn app.main:app --reload`.
9. Open `/login` and `/docs` on the configured local origin.

Deployment should add HTTPS and a secure cookie, production-grade secret management, hardened PostgreSQL networking/backups, a restrictive host/origin policy, an operational ASGI process manager, monitoring, dependency and migration review, and an explicit retention/access policy. The built-in development reload server is not a production process manager.

## 12. Results, limitations, and future scope

### Results to record

Record the application flows you personally exercised, screenshots if permitted, the actual pytest outcome, and any verified demonstration observations: [Add measured or observed results; do not invent them.]

### Limitations

- The application is a small internship project, not an audited HR or payroll product.
- There is no public self-registration, password-reset flow, multi-factor authentication, or token-refresh flow.
- Admins supply an initial employee password; a forced password-change workflow is not implemented.
- Employee deletion is irreversible and deletes linked account/attendance/leave records.
- Employee directory pagination is available in the interface. Attendance, department, and leave tables, and the employee selectors used by forms, currently show up to 100 records at a time.
- Attendance entries are immutable from the current interface; correction/audit workflows are not included.
- There is no notification service, file upload, automated deployment, or production hosting adapter.
- Automated API test results remain unknown until the PostgreSQL test suite is executed on a configured machine.

### Future scope

Add password change/reset and multi-factor authentication, audited attendance corrections, explicit employee offboarding/retention rather than destructive deletion, pagination for longer attendance/department/leave lists, email notifications, organization-defined leave calendars and policies, audit logging, accessibility review, deployment automation, backups and monitoring, and an independent security review.

## 13. Conclusion

The project demonstrates a structured FastAPI application with a real PostgreSQL integration, versioned migrations, separate validation and ORM layers, role/object authorization, and a browser interface using API responses. Setting up a dedicated test database and completing the outstanding operational and testing work are part of a responsible final demonstration; actual verification and personal internship details must be supplied by the student.

## 14. References

1. FastAPI documentation — https://fastapi.tiangolo.com/
2. PostgreSQL documentation — https://www.postgresql.org/docs/
3. SQLAlchemy 2.x documentation — https://docs.sqlalchemy.org/en/20/
4. Alembic documentation — https://alembic.sqlalchemy.org/
5. Pydantic documentation — https://docs.pydantic.dev/
6. PyJWT documentation — https://pyjwt.readthedocs.io/
7. pwdlib documentation — https://frankie567.github.io/pwdlib/
8. Pytest documentation — https://docs.pytest.org/
