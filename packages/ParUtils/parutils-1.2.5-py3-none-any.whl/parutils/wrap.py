from time import time
from functools import wraps

import parutils as u


def simple(func):
    @wraps(func)
    def new_f(*args, **kwargs):
        start_time = time()
        u.log(f"[{func.__name__}] start")
        out = func(*args, **kwargs)
        dstr = u.get_duration_string(start_time)
        u.log(f"[{func. __name__}] end ({dstr})")
        u.log_print()
        return out
    return new_f
