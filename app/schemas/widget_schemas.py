from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class WidgetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    button_text: str = Field(default="Submit", max_length=50)

class WidgetUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    button_text: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None

class WidgetOut(BaseModel):
    id: UUID
    tenant_id: UUID
    type: str
    title: str
    description: str | None
    button_text: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
