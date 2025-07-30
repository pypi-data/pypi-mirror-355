from typing import Any
from textual import on
from textual.app import App


from analyst_klondike.features.current.selectors import select_has_file_openned
from analyst_klondike.features.data_context.save_action import save_to_json
from analyst_klondike.features.app.actions import ChangeThemeAction
from analyst_klondike.features.demo_quiz.demo import start_demo_quiz
from analyst_klondike.state.app_dispatch import app_dispatch
from analyst_klondike.state.app_state import AppState, get_state, select
from analyst_klondike.ui.editor_screen.editor import EditorScreen
from analyst_klondike.ui.file_screen.save_file_before_exit_screen import (
    SaveOnExitModal,
    SaveOrExitModalResult
)


class RunnerApp(App[Any]):
    COMMAND_PALETTE_BINDING = "ctrl+backslash"
    EDITOR_SCREEN = EditorScreen()

    def __init__(self) -> None:
        super().__init__()

    def update_view(self, state: AppState) -> None:
        RunnerApp.EDITOR_SCREEN.update_view(state)

    def on_mount(self) -> None:
        self.push_screen(RunnerApp.EDITOR_SCREEN)
        self.theme = "gruvbox"
        self.title = "Клондайк аналитика"
        self.sub_title = "Интерактивный тренажер Python на вашем компьютере"

    @on(EditorScreen.UpdateAppTitleMessage)
    def on_title_subtitle_changed(self, event: EditorScreen.UpdateAppTitleMessage) -> None:
        self.title = event.title
        self.sub_title = event.subtitle

    async def action_quit(self):

        def on_screen_get_result(res: SaveOrExitModalResult | None) -> None:
            if res == "cancel":
                return
            if res == "save":
                state = get_state()
                save_to_json(state)
                self.app.notify(
                    "Сохранено",
                    title=state.current.opened_file_name,
                    severity="information",
                    timeout=1
                )
            self.app.exit(0)
        has_file = select(select_has_file_openned)
        if has_file:
            self.push_screen(SaveOnExitModal(), on_screen_get_result)
        else:
            self.exit(0)

    def watch_theme(self, new_theme: Any) -> None:
        app_dispatch(ChangeThemeAction(
            theme=new_theme,
            is_dark=self.current_theme.dark
        ))

    # This action is used in wellcome message
    def action_start_demo_test(self):
        start_demo_quiz()


_app = RunnerApp()


def get_app() -> RunnerApp:
    return _app
