# models.py

import re
from pydantic import BaseModel, EmailStr, field_validator, constr, conint, confloat
from typing import Dict, List, Optional

class YearSetting(BaseModel):
    year: str
    active: bool = True
    credits: conint(ge=0)
    weight: confloat(ge=0, le=100)

class CalculatorConfig(BaseModel):
    years: List[YearSetting]

class User(BaseModel):
    userid: Optional[str] = None
    firstName: str
    email: EmailStr
    password: str
    university: str
    degree: str
    calcType: str
    calculator: Optional[CalculatorConfig] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character.")
        return value

    @field_validator("calcType")
    @classmethod
    def validate_calc_type(cls, value):
        allowed = ["UK Percentage", "US GPA 4.0", "US GPA 5.0"]
        if value not in allowed:
            raise ValueError("calcType must be one of: " + ", ".join(allowed))
        return value

class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=20)

class CalendarEvent(BaseModel):
    id: Optional[str] = None
    user_email: str
    title: str
    description: Optional[str] = None
    date: str  # ISO format date
    start_time: Optional[str] = None  # For time-specific events
    end_time: Optional[str] = None
    all_day: bool = True
    type: str = "general"  # e.g., "assignment", "exam", "study"
    color: Optional[str] = None  # Color code for the event
    completed: bool = False

class UserProfileUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    avatar: Optional[str] = None
    dateOfBirth: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must have at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must have at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must have at least one special character")
        return value

class AppearanceSettings(BaseModel):
    accentColor: Optional[str] = "purple"
    fontSize: Optional[str] = "medium"
    highContrast: Optional[bool] = False

class AcademicSettings(BaseModel):
    gradingScale: Optional[List[dict]] = None
    termStartDate: Optional[str] = None
    termEndDate: Optional[str] = None
    holidays: Optional[List[dict]] = None

class AccessibilitySettings(BaseModel):
    screenReaderOptimized: Optional[bool] = False
    keyboardShortcuts: Optional[bool] = True
    focusMode: Optional[bool] = False

class CalendarSettings(BaseModel):
    firstDayOfWeek: Optional[str] = "sunday"
    defaultEventDuration: Optional[str] = "60"
    defaultEventType: Optional[str] = "general"
    timeFormat: Optional[str] = "12h"
    dateFormat: Optional[str] = "MM/DD/YYYY"


class UserSettings(BaseModel):
    dark_mode: Optional[bool] = False
    notifications_enabled: Optional[bool] = True
    calendar_view: Optional[str] = "month"
    language: Optional[str] = "en"
    appearance: Optional[AppearanceSettings] = None
    academic: Optional[AcademicSettings] = None
    accessibility: Optional[AccessibilitySettings] = None
    calendar: Optional[CalendarSettings] = None

class Assessment(BaseModel):
    name: str
    weight: confloat(ge=0, le=100)
    score: confloat(ge=0, le=100)

class Examination(BaseModel):
    name: str = "Final Examination"
    weight: confloat(ge=0, le=100)
    score: confloat(ge=0, le=100)

class Module(BaseModel):
    id: Optional[str] = None
    user_email: str
    name: str
    code: Optional[str] = None
    credits: confloat(ge=0)
    year: str  # e.g., "Year 1"
    semester: int = 1  # Added semester field, default to 1
    score: confloat(ge=0, le=100)
    assessments: List[Assessment] = []
    examination: Optional[Examination] = None
    university: Optional[str] = None  # University name
    degree: Optional[str] = None      # Degree/major name
    description: Optional[str] = None  # Module description
    completed: bool = False           # Whether the module is completed
    status: str = "active"            # Status of the module: active, completed, dropped

    class Config:
        extra = "allow"  # Allow extra fields

class GradeTarget(BaseModel):
    title: str
    description: str
    target_score: confloat(ge=0, le=100)
    progress: confloat(ge=0, le=100)

class Activity(BaseModel):
    type: str  # Type of activity: grade, submission, etc.
    title: str
    description: str
    time: str

class UserDashboardConfig(BaseModel):
    view_preferences: Optional[dict] = None
    recent_activities: Optional[List[Activity]] = None
    goals: Optional[List[GradeTarget]] = None
    grade_visualization: Optional[dict] = None

class EducationDetails(BaseModel):
    level: str  # Undergraduate, Postgraduate, etc.
    mode: str  # Full-time, Part-time
    studyTimes: List[str] = []  # Morning, Afternoon, Evening

class YearWeight(BaseModel):
    year: str
    weight: float


class DegreeStructure(BaseModel):
    totalYears: int
    semestersPerYear: int
    creditsPerYear: int
    currentYear: str
    yearWeights: Dict[str, float]
    degreeType: str = "UK Percentage"
    targetGrade: Optional[float] = 70



class OnboardingQuestionnaire(BaseModel):
    educationDetails: Optional[EducationDetails] = None
    degreeStructure: Optional[DegreeStructure] = None