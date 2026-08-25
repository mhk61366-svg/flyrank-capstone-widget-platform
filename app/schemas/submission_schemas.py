from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class SubmissionCreate(BaseModel):
    widget_id: UUID
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    age: int = Field(ge=0, le=150)
    gender: str = Field(min_length=1, max_length=50)
    message: str | None = Field(default=None, max_length=2000)
    hp_field: str = Field(default="", max_length=200)

class SubmissionOut(BaseModel):
    id: UUID
    widget_id: UUID
    status: str
    created_at: datetime