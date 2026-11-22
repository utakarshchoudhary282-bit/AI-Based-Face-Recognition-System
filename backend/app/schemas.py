"""Shapes of the data the API receives and sends."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EmployeeIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    label: Optional[str] = None            # photo folder name; made from the name if empty
    department: str = ""
    designation: str = ""
    access_level: str = Field(default="L1", pattern="^L[1-4]$")
    email: str = ""
    phone: str = ""
    office_location: str = ""
    shift: str = "General (9:30-18:30)"
    manager: str = ""
    joining_date: str = ""
    status: str = Field(default="Active", pattern="^(Active|On Leave|Suspended|Exited)$")
    notes: str = ""


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    access_level: Optional[str] = Field(default=None, pattern="^L[1-4]$")
    email: Optional[str] = None
    phone: Optional[str] = None
    office_location: Optional[str] = None
    shift: Optional[str] = None
    manager: Optional[str] = None
    joining_date: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(Active|On Leave|Suspended|Exited)$")
    notes: Optional[str] = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    label: str
    employee_code: str
    name: str
    department: str
    designation: str
    access_level: str
    email: str
    phone: str
    office_location: str
    shift: str
    manager: str
    joining_date: str
    status: str
    notes: str
    has_photo: bool = False
    face_images: int = 0


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    employee_id: Optional[int] = None
