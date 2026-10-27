from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    message: str
    user: "UserSummary"


class UserSummary(BaseModel):
    id: int
    email: EmailStr
    role: str
    employee_id: int | None = None
    employee_name: str | None = None


LoginResponse.model_rebuild()

