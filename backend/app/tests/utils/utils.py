import random
import string


def random_lower_string(length: int = 32) -> str:
    """Generate a random lowercase string."""
    return "".join(random.choices(string.ascii_lowercase, k=length))
