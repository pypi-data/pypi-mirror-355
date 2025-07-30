from analyst_klondike.state.app_state import AppState


def current_file_path(state: AppState) -> tuple[str, str]:
    return (
        state.current.opened_file_path,
        state.current.opened_file_name
    )
