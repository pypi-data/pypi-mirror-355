import time
from datetime import datetime
from typing import Any, Optional

# DO NOT USE mutable default arguments
# Mutable default arguments are evaluated only once when the module is loaded
# This means that the default argument is shared between all calls to the funciton

def append_to(element: int, to: list[int] = []) -> list[int]:
    to.append(element)
    return to