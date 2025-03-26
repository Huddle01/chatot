import random
import string

def get_random_string(length: int) -> str:
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
    return result_str
