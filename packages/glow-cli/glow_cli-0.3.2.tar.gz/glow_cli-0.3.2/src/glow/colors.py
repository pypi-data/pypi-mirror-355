import os
from typing import List, Union


PRINT_COLOR = os.environ.get("PRINT_COLOR", "true").lower() == "true"


class bcolors:
    """
    Colors we can print out in shell
    """

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    def __init__(self, text: Union[str, "bcolors"], color: str):
        self.text = str(text)
        self.color = getattr(self, color.upper())

    def __str__(self):
        return self.color + self.text + bcolors.ENDC


def cprint(text: str, color: Union[str, List[str]] = "green") -> None:
    """
    Print text in color
    """
    if PRINT_COLOR:
        if isinstance(color, str):
            print(bcolors(text, color))
        elif isinstance(color, list):
            for c in color:
                text = str(bcolors(text, c))
            print(text)
    else:
        print(text)


def mask_print(x: str) -> str:
    x = str(x)
    return "*" * len(x)
