from os import getcwd
from os.path import dirname, join, exists, basename

from analyst_klondike.features.data_context.set_opened_file_action import SetOpenedFileAction
from analyst_klondike.state.app_dispatch import app_dispatch


class TooManyArgumentsException(Exception):
    pass


def set_file_from_argv(argv: list[str]) -> None:
    if len(argv) < 2:
        return
    if len(argv) > 2:
        raise TooManyArgumentsException(
            f"Too many arguments: {",".join(argv)}. One argument expected"
        )

    python_file_dir = dirname(argv[0])
    cmd = getcwd()
    fpath = _first_existed_path(argv[1:],
                                python_file_dir,
                                cmd)
    if fpath is not None:
        fname = basename(fpath)
        app_dispatch(SetOpenedFileAction(
            opened_file_name=fname,
            opened_file_path=fpath
        ))
    else:
        raise FileNotFoundError(
            f"File '{argv[1]}' not exists. Trying to look up in {python_file_dir} first, then {cmd}"
        )


def _first_existed_path(file_names: list[str], *dirs: str) -> str | None:
    return next((
        join(d, f) for f in file_names for d in dirs if exists(join(d, f))
    ), None)
