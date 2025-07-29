from dataclasses import dataclass
from os.path import exists
import json
from typing import Any


@dataclass
class UserInfoJson:
    email: str


@dataclass
class QuestionJson:
    id: int
    title: str
    text: str
    code_template: str
    code: str
    test_cases: list[dict[str, Any]]
    is_passed: str


@dataclass
class PythonQuizJson:
    id: str
    title: str
    questions: list[QuestionJson]


@dataclass
class JsonLoadResult:
    user_info: UserInfoJson
    quizes: list[PythonQuizJson]


def get_quiz_json(file_path: str) -> JsonLoadResult:
    if not exists(file_path):
        raise FileExistsError(f"<{file_path}> not found")
    load_result = JsonLoadResult(
        user_info=UserInfoJson(email=""),
        quizes=[]
    )
    with open(file_path, encoding='UTF-8') as f:
        json_data = json.load(f)
        load_result.user_info.email = json_data["user_info"]["email"]
        # map quizes
        for quiz_json in json_data["quizes"]:
            quiz_obj = PythonQuizJson(
                id=quiz_json["id"],
                title=quiz_json["title"],
                questions=[]
            )
            # map questions
            for question_json in quiz_json["questions"]:
                quiz_obj.questions.append(
                    QuestionJson(
                        id=int(question_json["id"]),
                        title=question_json["title"],
                        text=question_json["text"],
                        code_template=question_json["code_template"],
                        code=question_json["code"],
                        test_cases=question_json["test_cases"],
                        is_passed=question_json.get("is_passed", "")
                    )
                )
            load_result.quizes.append(quiz_obj)

    return load_result
