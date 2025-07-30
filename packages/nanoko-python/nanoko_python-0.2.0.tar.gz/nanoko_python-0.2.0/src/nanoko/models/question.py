from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, model_serializer


# Unsolvable circular import
class Performance(Enum):
    """A standard to represent the performance of students."""

    NOT_STARTED = 0
    ATTEMPTED = 1
    FAMILIAR = 2
    PROFICIENT = 3
    MASTERED = 4


class ConceptType(Enum):
    """Concept enum for the concept of subquestions."""

    OPERATIONS_ON_NUMBERS = 0
    MATHEMATICAL_RELATIONSHIPS = 1
    SPATIAL_PROPERTIES_AND_REPRESENTATIONS = 2
    LOCATION_AND_NAVIGATION = 3
    MEASUREMENT = 4
    STATISTICS_AND_DATA = 5
    ELEMENTS_OF_CHANCE = 6


class ProcessType(Enum):
    """Process enum for the process of subquestions."""

    FORMULATE = 0
    APPLY = 1
    EXPLAIN = 2


class SubQuestion(BaseModel):
    """API model for subquestion."""

    id: Optional[int] = None
    description: str
    answer: str
    concept: ConceptType
    process: ProcessType
    keywords: Optional[List[str]] = None
    options: Optional[List[str]] = None
    image_id: Optional[int] = None

    # For completed sub-questions
    submitted_answer: Optional[str] = None
    performance: Optional[Performance] = None
    feedback: Optional[str] = None

    @model_serializer
    def serialize_model(self):
        """Serialize the subquestion with enum values."""
        data = {}
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, Enum):
                data[field_name] = field_value.value
            else:
                data[field_name] = field_value
        return {k: v for k, v in data.items() if v is not None}


class Question(BaseModel):
    """API model for question."""

    id: Optional[int] = None
    name: str
    source: str
    is_audited: Optional[bool] = None
    is_deleted: Optional[bool] = None
    sub_questions: List[SubQuestion]
