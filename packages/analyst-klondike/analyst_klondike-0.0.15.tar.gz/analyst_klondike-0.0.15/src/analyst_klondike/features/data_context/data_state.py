from dataclasses import dataclass, field
from typing import Any, Literal

PythonTaskResult = Literal["passed", "failed", "not_runned"]


@dataclass
class PythonTaskState:
    id: int
    title: str
    description: str
    code_template: str
    code: str
    quiz_id: str
    test_cases: list[dict[str, Any]] = field(
        default_factory=list[dict[str, Any]]
    )
    is_passed: PythonTaskResult = "not_runned"


@dataclass
class PythonQuizState:
    id: str
    title: str
    is_node_expanded: bool


@dataclass
class DataState:
    quizes: dict[str, PythonQuizState] = field(
        default_factory=dict[str, PythonQuizState]
    )
    tasks: dict[int, PythonTaskState] = field(
        default_factory=dict[int, PythonTaskState]
    )
