from os.path import basename
from dataclasses import dataclass
import analyst_klondike
from analyst_klondike.features.data_context.data_state import (
    PythonQuizState,
    PythonTaskResult,
    PythonTaskState
)
from analyst_klondike.features.data_context.json_load.dc import (
    JsonLoadResult,
    PythonQuizJson,
    QuestionJson)
from analyst_klondike.state.app_state import AppState
from analyst_klondike.state.base_action import BaseAction


@dataclass
class InitAction(BaseAction):
    type = "INIT_APP"
    data: JsonLoadResult
    file_path: str


def init_state(state: AppState, data: JsonLoadResult, file_path: str) -> None:
    state.user_email = "Клондайк аналитика"
    state.data.quizes = {
        x.id: _get_quiz_state(x) for x in data.quizes
    }
    state.data.tasks = {
        question.id: _get_question_state(question, quiz.id)
        for quiz in data.quizes
        for question in quiz.questions
    }
    state.current.app_title = "Клондайк аналитика"
    state.current.app_subtitle = "Интерактивный тренажер Python на вашем " +\
        f"компьютере (version. {analyst_klondike.__version__})"
    state.current.opened_file_path = file_path
    state.current.opened_file_name = basename(file_path)


def _get_quiz_state(data: PythonQuizJson) -> PythonQuizState:
    return PythonQuizState(
        id=data.id,
        title=data.title,
        is_node_expanded=False
    )


def _get_question_state(data: QuestionJson, quiz_id: str) -> PythonTaskState:
    def get_passed_status() -> PythonTaskResult:
        if data.is_passed == "passed":
            return "passed"
        if data.is_passed == "failed":
            return "failed"
        return "not_runned"

    return PythonTaskState(
        id=data.id,
        quiz_id=quiz_id,
        title=data.title,
        description=data.text,
        code_template=data.code_template,
        code=data.code if data.code != "" else data.code_template,
        test_cases=data.test_cases,
        is_passed=get_passed_status(),
    )
