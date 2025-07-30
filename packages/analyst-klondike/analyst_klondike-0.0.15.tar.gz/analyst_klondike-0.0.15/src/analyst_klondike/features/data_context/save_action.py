from dataclasses import dataclass
import json
from typing import Any

from analyst_klondike.state.app_state import AppState
from analyst_klondike.state.base_action import BaseAction


@dataclass
class SaveAction(BaseAction):
    type = "SAVE_ACTION"


def save_to_json(state: AppState):
    with open(state.current.opened_file_path,
              encoding='utf-8',
              mode='w') as f:
        data = _create_json(state)
        json.dump(data, f, indent=4, ensure_ascii=False)


def _create_json(state: AppState) -> Any:
    def _get_tasks(quiz_id: str):
        return (
            t for t in state.data.tasks.values() if t.quiz_id == quiz_id
        )

    d = {  # type: ignore
        "user_info": {
            "email": state.user_email
        },
        "quizes": [
            {
                "id": quiz.id,
                "title": quiz.title,
                "questions": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "text": t.description,
                        "code_template": t.code_template,
                        "code": t.code,
                        "test_cases": t.test_cases,
                        "is_passed": t.is_passed
                    } for t in _get_tasks(quiz.id)
                ]
            } for quiz in state.data.quizes.values()
        ]
    }
    return d  # type: ignore
