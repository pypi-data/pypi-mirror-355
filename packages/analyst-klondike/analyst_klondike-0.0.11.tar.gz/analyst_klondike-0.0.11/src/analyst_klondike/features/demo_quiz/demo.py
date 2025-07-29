import os
from analyst_klondike.features.code.actions import RunAllCodeAction
from analyst_klondike.features.data_context.init_action import InitAction
from analyst_klondike.features.data_context.json_load.dc import get_quiz_json
from analyst_klondike.features.message_box.actions import HideMessageBoxAction
from analyst_klondike.state.app_dispatch import app_dispatch


def _demo_file_path() -> str:
    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(this_file_dir, "demo.json")


def start_demo_quiz():
    fpath = _demo_file_path()
    load_result = get_quiz_json(fpath)

    app_dispatch(
        InitAction(data=load_result,
                   file_path=fpath)
    )
    app_dispatch(RunAllCodeAction())
    app_dispatch(HideMessageBoxAction())
