from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import hash_password
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User


def login_as(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.cookies['access_token']}"}


def seed_employee(
    db_session_factory,
    employee_code: str = "EMP-001",
    email: str = "employee@example.test",
    name: str = "Test Employee",
):
    with db_session_factory() as db:
        department = db.scalar(select(Department).where(Department.name == "Engineering"))
        if department is None:
            department = Department(name="Engineering")
        db.add(department)
        user = User(email=email, password_hash=hash_password("Employee-testing-password-123"))
        employee = Employee(
            employee_code=employee_code,
            name=name,
            email=email,
            department=department,
            designation="Engineer",
            joining_date=date.today(),
            salary=50000,
            employment_status="active",
            user=user,
        )
        db.add(employee)
        db.commit()
        return employee.id, department.id


def test_login_and_admin_dashboard(
    client: TestClient, admin_headers: dict[str, str], db_session_factory
):
    employee_id, _ = seed_employee(db_session_factory)
    attendance_response = client.post(
        "/api/v1/attendance",
        json={"employee_id": employee_id, "attendance_date": date.today().isoformat(), "status": "present"},
        headers=admin_headers,
    )
    assert attendance_response.status_code == 201
    employee_headers = login_as(client, "employee@example.test", "Employee-testing-password-123")
    leave_start = date.today() + timedelta(days=1)
    leave_response = client.post(
        "/api/v1/leave-requests",
        json={
            "start_date": leave_start.isoformat(),
            "end_date": leave_start.isoformat(),
            "reason": "Personal appointment",
        },
        headers=employee_headers,
    )
    assert leave_response.status_code == 201
    response = client.get("/api/v1/dashboard/stats", headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {
        "total_employees": 1,
        "active_employees": 1,
        "total_departments": 1,
        "employees_present_today": 1,
        "pending_leave_requests": 1,
    }


def test_employee_access_is_limited_to_own_records(
    client: TestClient, admin_headers: dict[str, str], db_session_factory
):
    employee_id, _ = seed_employee(db_session_factory)
    other_employee_id, _ = seed_employee(
        db_session_factory,
        employee_code="EMP-002",
        email="other@example.test",
        name="Another Employee",
    )
    for target_id in (employee_id, other_employee_id):
        response = client.post(
            "/api/v1/attendance",
            json={
                "employee_id": target_id,
                "attendance_date": date.today().isoformat(),
                "status": "present",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
    own = client.get("/api/v1/employees/me", headers=login_as(client, "employee@example.test", "Employee-testing-password-123"))
    assert own.status_code == 200
    assert own.json()["id"] == employee_id
    other = client.get("/api/v1/employees/99999", headers=login_as(client, "employee@example.test", "Employee-testing-password-123"))
    assert other.status_code == 403
    own_employees = client.get("/api/v1/employees", headers=login_as(client, "employee@example.test", "Employee-testing-password-123"))
    assert own_employees.json()["total"] == 1
    own_attendance = client.get(
        f"/api/v1/attendance?employee_id={other_employee_id}",
        headers=login_as(client, "employee@example.test", "Employee-testing-password-123"),
    )
    assert own_attendance.json()["total"] == 1
    assert own_attendance.json()["items"][0]["employee_id"] == employee_id
    start = date.today() + timedelta(days=2)
    own_leave = client.post(
        "/api/v1/leave-requests",
        json={"start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "Personal"},
        headers=login_as(client, "employee@example.test", "Employee-testing-password-123"),
    )
    other_leave = client.post(
        "/api/v1/leave-requests",
        json={"start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "Personal"},
        headers=login_as(client, "other@example.test", "Employee-testing-password-123"),
    )
    assert own_leave.status_code == 201
    assert other_leave.status_code == 201
    own_requests = client.get("/api/v1/leave-requests", headers=login_as(client, "employee@example.test", "Employee-testing-password-123"))
    assert own_requests.json()["total"] == 1
    assert own_requests.json()["items"][0]["employee_id"] == employee_id
    dashboard = client.get("/api/v1/dashboard/stats", headers=login_as(client, "employee@example.test", "Employee-testing-password-123"))
    assert dashboard.status_code == 403


def test_employee_crud_and_department_delete_protection(client: TestClient, admin_headers: dict[str, str]):
    department_response = client.post(
        "/api/v1/departments", json={"name": "Sales"}, headers=admin_headers
    )
    assert department_response.status_code == 201
    department_id = department_response.json()["id"]
    payload = {
        "employee_code": "EMP-002",
        "name": "A Test Person",
        "email": "a-person@example.test",
        "department_id": department_id,
        "designation": "Analyst",
        "joining_date": date.today().isoformat(),
        "salary": "42000.00",
        "password": "Employee-testing-password-456",
    }
    invalid = client.post(
        "/api/v1/employees",
        json=payload | {"salary": "-1"},
        headers=admin_headers,
    )
    assert invalid.status_code == 422
    created = client.post("/api/v1/employees", json=payload, headers=admin_headers)
    assert created.status_code == 201
    assert created.json()["department_name"] == "Sales"
    assert client.delete(f"/api/v1/departments/{department_id}", headers=admin_headers).status_code == 409
    duplicate = client.post("/api/v1/employees", json=payload | {"employee_code": "EMP-003"}, headers=admin_headers)
    assert duplicate.status_code == 409
    updated = client.patch(
        f"/api/v1/employees/{created.json()['id']}",
        json={"employment_status": "inactive"},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["employment_status"] == "inactive"
    deleted = client.delete(f"/api/v1/employees/{created.json()['id']}", headers=admin_headers)
    assert deleted.status_code == 204
    assert client.delete(f"/api/v1/departments/{department_id}", headers=admin_headers).status_code == 204
    assert client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    ).status_code == 401


def test_attendance_duplicates_and_employee_cannot_record_attendance(
    client: TestClient, admin_headers: dict[str, str], db_session_factory
):
    employee_id, _ = seed_employee(db_session_factory)
    payload = {"employee_id": employee_id, "attendance_date": date.today().isoformat(), "status": "present"}
    assert client.post("/api/v1/attendance", json=payload, headers=admin_headers).status_code == 201
    duplicate = client.post("/api/v1/attendance", json=payload, headers=admin_headers)
    assert duplicate.status_code == 409
    employee_headers = login_as(client, "employee@example.test", "Employee-testing-password-123")
    forbidden = client.post("/api/v1/attendance", json=payload, headers=employee_headers)
    assert forbidden.status_code == 403
    assert client.get("/api/v1/attendance", headers=employee_headers).json()["total"] == 1


def test_leave_submission_overlap_and_administrator_review(
    client: TestClient, admin_headers: dict[str, str], db_session_factory
):
    seed_employee(db_session_factory)
    employee_headers = login_as(client, "employee@example.test", "Employee-testing-password-123")
    start = date.today() + timedelta(days=2)
    payload = {"start_date": start.isoformat(), "end_date": (start + timedelta(days=2)).isoformat(), "reason": "Family event"}
    submitted = client.post("/api/v1/leave-requests", json=payload, headers=employee_headers)
    assert submitted.status_code == 201
    duplicate = client.post(
        "/api/v1/leave-requests",
        json={"start_date": (start + timedelta(days=1)).isoformat(), "end_date": (start + timedelta(days=3)).isoformat(), "reason": "Overlapping request"},
        headers=employee_headers,
    )
    assert duplicate.status_code == 409
    item_id = submitted.json()["id"]
    approved = client.patch(
        f"/api/v1/leave-requests/{item_id}",
        json={"status": "approved", "reviewer_comment": "Enjoy"},
        headers=admin_headers,
    )
    assert approved.status_code == 200
    assert approved.json()["reviewer_email"] == "admin@example.test"
    cannot_change = client.patch(
        f"/api/v1/leave-requests/{item_id}",
        json={"status": "rejected"},
        headers=admin_headers,
    )
    assert cannot_change.status_code == 409
    assert client.get("/api/v1/leave-requests", headers=employee_headers).json()["items"][0]["id"] == item_id
    rejected_start = start + timedelta(days=10)
    rejected = client.post(
        "/api/v1/leave-requests",
        json={
            "start_date": rejected_start.isoformat(),
            "end_date": rejected_start.isoformat(),
            "reason": "Another planned absence",
        },
        headers=employee_headers,
    )
    rejection_response = client.patch(
        f"/api/v1/leave-requests/{rejected.json()['id']}",
        json={"status": "rejected", "reviewer_comment": "Please choose another date."},
        headers=admin_headers,
    )
    assert rejection_response.status_code == 200
    assert rejection_response.json()["status"] == "rejected"


def test_invalid_login_token_and_non_admin_permissions(
    client: TestClient, admin_headers: dict[str, str], db_session_factory
):
    failed_login = client.post("/api/v1/auth/login", json={"email": "admin@example.test", "password": "wrong"})
    assert failed_login.status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}).status_code == 401
    from datetime import UTC, datetime

    import jwt

    from app.core.config import get_settings

    expired_token = jwt.encode(
        {"sub": "1", "role": "admin", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        get_settings().jwt_secret_key,
        algorithm=get_settings().jwt_algorithm,
    )
    expired = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert expired.status_code == 401
    seed_employee(db_session_factory)
    employee_headers = login_as(client, "employee@example.test", "Employee-testing-password-123")
    assert client.post("/api/v1/departments", json={"name": "Forbidden"}, headers=employee_headers).status_code == 403
