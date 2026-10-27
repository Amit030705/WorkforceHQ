from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_employees: int
    active_employees: int
    total_departments: int
    employees_present_today: int
    pending_leave_requests: int

