from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from nanoko.models.user import User
from nanoko.models.question import SubQuestion, Question


# Unsolvable circular import
class Performance(Enum):
    """A standard to represent the performance of students."""

    NOT_STARTED = 0
    ATTEMPTED = 1
    FAMILIAR = 2
    PROFICIENT = 3
    MASTERED = 4


class ProcessPerformances(BaseModel):
    """Performance of a student in process ideas."""

    formulate: float = Field(0, ge=0, le=4.0)
    apply: float = Field(0, ge=0, le=4.0)
    explain: float = Field(0, ge=0, le=4.0)


class Performances(BaseModel):
    """Performance of a student in all content ideas."""

    operations_on_numbers: ProcessPerformances
    mathematical_relationships: ProcessPerformances
    spatial_properties_and_representations: ProcessPerformances
    location_and_navigation: ProcessPerformances
    measurement: ProcessPerformances
    statistics_and_data: ProcessPerformances
    elements_of_chance: ProcessPerformances


class Assignment(BaseModel):
    """Assignment model for API."""

    id: int
    name: str
    description: str
    teacher_id: int
    question_ids: List[int]
    due_date: Optional[datetime] = None


class Class(BaseModel):
    """Class model for API."""

    id: int
    name: str
    enter_code: str
    teacher_id: int


class ClassData(BaseModel):
    """Class data model for API."""

    class_name: str
    teacher_name: str
    to_do_assignments: List[Assignment]
    done_assignments: List[Assignment]


class TeacherClassData(BaseModel):
    """Teacher class data model for API."""

    class_id: int
    name: str
    enter_code: str
    students: List[User]
    assignments: List[Assignment]
    performances: Performances


class StudentPerformance(BaseModel):
    """Student performance model for API."""

    user: User
    answer: Optional[str] = None
    performance: Optional[Performance] = None
    feedback: Optional[str] = None
    date: Optional[datetime] = None
    # If none, then the student did not submit


class ReviewSubQuestion(SubQuestion):
    """Review sub-question model for API."""

    student_performances: List[StudentPerformance]


class ReviewQuestion(Question):
    """Review question model for API."""

    sub_questions: List[ReviewSubQuestion]


class AssignmentReviewData(BaseModel):
    """Assignment review data model for API."""

    title: str
    questions: List[ReviewQuestion]


class FeedBack(BaseModel):
    """Feedback model for API."""

    comment: str
    performance: Performance
