import random
import string


def generate_reference_code() -> str:
    """Short, human-readable reference like 'A231'."""
    letter = random.choice(string.ascii_uppercase)
    digits = "".join(random.choices(string.digits, k=3))
    return f"{letter}{digits}"
