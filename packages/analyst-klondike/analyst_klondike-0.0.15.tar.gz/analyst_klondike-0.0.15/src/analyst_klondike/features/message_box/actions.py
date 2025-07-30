from dataclasses import dataclass
from analyst_klondike.state.base_action import BaseAction


@dataclass
class DisplayMessageBoxAction(BaseAction):
    type = "DISPLAY_MESSAGE_BOX_ACTION"
    message: str


@dataclass
class HideMessageBoxAction(BaseAction):
    type = "HIDE_MESSAGE_BOX_ACTION"
