import sys
from analyst_klondike.features.data_context.arg_file_load.arg_load import (
    TooManyArgumentsException,
    set_file_from_argv
)
from analyst_klondike.ui.runner_app import get_app


def analyst_klondike():
    try:
        app = get_app()
        set_file_from_argv(sys.argv)
        app.run()
    except (FileNotFoundError, TooManyArgumentsException) as err:
        print(err)
        sys.exit(1)


if __name__ == "__main__":
    analyst_klondike()
