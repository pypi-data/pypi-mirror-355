from __future__ import annotations
from os.path import basename
from typing import Any

from textual import on
from textual.message import Message
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import (
    Header,
    Footer
)
from textual.binding import Binding


from analyst_klondike.features.app.actions import EditorScreenReadyAction
from analyst_klondike.features.current.selectors import select_has_file_openned
from analyst_klondike.features.data_context.json_load.dc import get_quiz_json
from analyst_klondike.features.code.actions import (
    RunAllCodeAction,
    RunCodeAndSetResultsAction,
    UpdateCodeAction)
from analyst_klondike.features.current.actions import (
    MakeQuizCurrentAction,
    MakeTaskCurrentAction
)
from analyst_klondike.features.code_explorer.code_explorer_reducer import (
    QuizNodeCollapseAction,
    QuizNodeExpandAction
)
from analyst_klondike.features.data_context.init_action import InitAction
from analyst_klondike.features.data_context.save_action import save_to_json
from analyst_klondike.features.data_context.selectors import current_file_path
from analyst_klondike.state.app_dispatch import app_dispatch
from analyst_klondike.ui.editor_screen.components.code_editor import CodeEditor
from analyst_klondike.ui.editor_screen.components.current_task import CurrentTaskInfo
from analyst_klondike.ui.editor_screen.components.explorer import Explorer
from analyst_klondike.ui.editor_screen.components.quiz_description import QuizDescription
from analyst_klondike.ui.editor_screen.components.test_results import TestResults

from analyst_klondike.features.message_box.actions import (
    DisplayMessageBoxAction,
    HideMessageBoxAction)
from analyst_klondike.features.message_box.ui.mb_screen import MessageBoxScreen

from analyst_klondike.ui.file_screen.open_file_screen import OpenFileScreen
from analyst_klondike.state.app_state import (
    AppState,
    get_state,
    select)

_WELLCOME_MESSAGE = """\
[bold]Клондайк аналитика[/bold]

Вас приветствует [bold]Клондайк аналитика![/bold] - интерактивный тренажер Python на вашем компьютере.

Чтобы воспользоваться тренажером, вы можете:
:white_heavy_check_mark: загрузить файл с задачами :fire:, который направил ваш ментор, или
:white_heavy_check_mark: пройти [@click=app.start_demo_test]демо-тест[/].
Успехов! 

Загрузить файл с задачами:
:keycap_1:  Получить файл с тестом у ментора или воспользоваться [@click=app.start_demo_test]демо-версией[/].
:keycap_2:  Перейти в каталог, где находится файл с тестом, например:
[on blue]cd ~/path/to/my_tests[/]

:keycap_3:  Убедиться, что файл есть в каталоге (опционально)
[on blue]ls[/]

:keycap_4:  Запустить программу, указав файл с тестом:
[on blue]analyst_klodike first_test.json[/]

:keycap_5:  Можно запустить программу без файла, а затем открыть его. В таком случае файл указывать не надо.
[on blue]analyst_klodike[/]

:skull: Данная программа - коммерческий продукт. Никакая ее часть не может быть использована без разрешения автора.
Исходный код программы является закрытым. Никая часть исходного кода не может быть использована без разрешения автора.
Исключительные права на эту программу принадлежат Малюге Илье Викторовичу (info@клондайк-аналитика.рф). 
"""


class EditorScreen(Screen[Any]):
    CSS_PATH = "editor.tcss"

    open_file_binding = Binding(id="open_file",
                                key='ctrl+o',
                                action='open_quiz_file',
                                description="Открыть тест",
                                tooltip="Открыть файл с задачами. " +
                                "Вам нужно будет написать код, который пройдет все тесты")

    run_code_binding = Binding(id="run_code",
                               key='ctrl+r',
                               action='run_btn_click',
                               description="Запустить код")

    save_file_binding = Binding(id="save_file",
                                key="ctrl+s",
                                action="save_quiz_to_file",
                                description="Сохранить")

    message_box_screen = MessageBoxScreen(id="message_box_screen")

    BINDINGS = [
        open_file_binding,
        save_file_binding,
        run_code_binding
    ]

    class UpdateAppTitleMessage(Message):
        def __init__(self, title: str, subtitle: str) -> None:
            super().__init__()
            self.title = title
            self.subtitle = subtitle

    class RequestOpenFileScreen(Message):
        pass

    def on_mount(self) -> None:
        app_dispatch(EditorScreenReadyAction())
        fpath, _ = select(current_file_path)
        if fpath != "":
            self._open_file()
        app_dispatch(DisplayMessageBoxAction(_WELLCOME_MESSAGE))

    def update_view(self, new_state: AppState):
        if not new_state.is_editor_screen_ready:
            return
        explorer = self.query_one("Explorer", Explorer)
        code_editor = self.query_one("CodeEditor", CodeEditor)
        task_info = self.query_one("CurrentTaskInfo", CurrentTaskInfo)
        test_results = self.query_one("TestResults", TestResults)
        quiz_description = self.query_one("QuizDescription", QuizDescription)

        explorer.state = new_state
        code_editor.state = new_state
        task_info.state = new_state
        test_results.update_view(new_state)
        quiz_description.state = new_state

        # send message to update title and subtitle
        self.post_message(EditorScreen.UpdateAppTitleMessage(
            new_state.current.app_title,
            new_state.current.app_subtitle
        ))
        # update component visibility
        if new_state.current.object_name == "task":
            code_editor.remove_class("component-hidden")
            quiz_description.add_class("component-hidden")
        elif new_state.current.object_name == "quiz":
            code_editor.add_class("component-hidden")
            quiz_description.remove_class("component-hidden")
        elif new_state.current.object_name == "account":
            pass

        self._display_message_box(new_state)

    def _display_message_box(self, state: AppState) -> None:
        current_screen_id = self.app.screen_stack[-1].id

        # display message box:
        if state.message_box.is_visible:
            if current_screen_id != EditorScreen.message_box_screen.id:
                self.app.push_screen(
                    EditorScreen.message_box_screen,
                    EditorScreen._on_message_box_close
                )
        else:
            if current_screen_id == EditorScreen.message_box_screen.id:
                self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Vertical(id="left_panel"):
            yield Explorer()
            yield CurrentTaskInfo()
        with Vertical(id="right_panel"):
            yield CodeEditor()
            yield QuizDescription(classes="component-hidden")
            yield TestResults()

    @on(Explorer.TaskSelected)
    def on_python_task_selected(self, ev: Explorer.TaskSelected) -> None:
        if isinstance(ev.task_id, int):
            app_dispatch(MakeTaskCurrentAction(ev.task_id))

    @on(Explorer.QuizSelected)
    def on_quiz_selected(self, ev: Explorer.QuizSelected) -> None:
        app_dispatch(MakeQuizCurrentAction(quiz_id=ev.quiz_id))

    @on(Explorer.QuizNodeExpandedOrCollapsed)
    def on_quiz_node_expanded_collapsed(self, ev: Explorer.QuizNodeExpandedOrCollapsed) -> None:
        if ev.action_type == "expanded":
            app_dispatch(QuizNodeExpandAction(quiz_id=ev.quiz_id))
        elif ev.action_type == "collapsed":
            app_dispatch(QuizNodeCollapseAction(quiz_id=ev.quiz_id))

    @on(CodeEditor.CodeUpdated)
    def on_editor_code_updated(self, ev: CodeEditor.CodeUpdated) -> None:
        app_dispatch(UpdateCodeAction(ev.code))

    def action_run_btn_click(self) -> None:
        app_dispatch(RunCodeAndSetResultsAction())

    def action_open_quiz_file(self) -> None:
        def _on_file_selected(file_path: str | None) -> None:
            if not isinstance(self.app.screen, EditorScreen):
                return
            if file_path is None or file_path == '':
                return

            load_result = get_quiz_json(file_path)

            app_dispatch(
                InitAction(data=load_result,
                           file_path=file_path)
            )
            app_dispatch(RunAllCodeAction())
            self.app.notify(
                "Загружено",
                title=basename(file_path),
                severity="information",
                timeout=1
            )

        self.app.push_screen(OpenFileScreen(), _on_file_selected)

    def action_save_quiz_to_file(self) -> None:
        state = get_state()

        save_to_json(state)
        self.app.notify(
            "Сохранено",
            title=state.current.opened_file_name,
            severity="information",
            timeout=1
        )

    def check_action(self, action: str, parameters: tuple[object, ...]):
        if action == EditorScreen.run_code_binding.action:
            has_file = select(select_has_file_openned)
            # Кнопка должна быть активна, если задача активирована
            if has_file:
                return True
            return None
        return True

    def _open_file(self) -> None:
        fpath, fname = select(current_file_path)
        load_result = get_quiz_json(fpath)

        app_dispatch(
            InitAction(data=load_result,
                       file_path=fpath)
        )
        app_dispatch(RunAllCodeAction())
        self.app.notify(
            "Загружено",
            title=fname,
            severity="information",
            timeout=1
        )

    @staticmethod
    def _on_message_box_close(_: bool | None) -> None:
        app_dispatch(
            HideMessageBoxAction()
        )
