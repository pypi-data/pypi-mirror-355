from dataclasses import dataclass


@dataclass
class MessageBoxState:
    is_visible: bool = False
    message: str = ""
