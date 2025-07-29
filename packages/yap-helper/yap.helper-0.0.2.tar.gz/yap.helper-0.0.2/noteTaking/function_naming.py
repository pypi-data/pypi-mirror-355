import time
from datetime import datetime
from typing import Any, Optional

def public_function():
    pass

def _private_function():
    pass

# Good name - functions should be verbs, arguments should be nouns
# name describes what the function does
def calculate_total_minus_discount(item_prices: list[int], discount: int) -> int:
    total_price = sum(item_prices) - discount
    return max(total_price, 0)

# use default arguments
# it is nice to put all of the default arguments AFTER the required arguments
def log_message(
        message: str, level: str = "INFO"
) -> None:
    # create a string representation of the timestamp
    formatted_ts = datetime.now().strftime("%Y-%m-%d $H:%M:%S")

    print(f"[{formatted_ts}] [{level}] {message}")

# a more extreme case of function headers
def log_better_message(
        message: str, timestamp: Optional[float] = None, level: str = "INFO"
) -> None:
    # use current time if no timestamp is provided
    if timestamp is None:
        timestamp = time.time()
    
    # create a string representation of the timestamp
    formatted_ts = datetime.now().strftime("%Y-%m-%d $H:%M:%S")

    print(f"[{formatted_ts}] [{level}] {message}")

def log_test() -> None:
    log_better_message("System started.")
    log_better_message("yap.helpActivated", timestamp=time.time())

log_test()