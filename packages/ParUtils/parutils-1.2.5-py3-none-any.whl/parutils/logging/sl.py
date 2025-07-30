from time import time
from parutils import strg
from threading import RLock

from .main import log
from .core import get_logger

lock = RLock()
sl_time_dict = {}


def step_log(counter,
             step,
             what='lines written',
             th_name='DEFAULT',
             extra=''):
    """Logs something only when the 'counter' is a multiple of 'step'

    - Initialise timer with init_sl_timer()
    - For more info, check out the README.md file
    """
    if counter % step != 0:
        return False

    # Avoids error if sl time has not been initialised
    st = get_logger().start_time if th_name not in sl_time_dict else sl_time_dict[th_name]
    dstr = strg.get_duration_string(st)
    bn_1 = strg.big_number(step)
    bn_2 = strg.big_number(counter)
    s = "{bn1} {what} in {dstr}. {bn2} {what} in total{extra}."
    msg = s.format(bn1=bn_1, bn2=bn_2, dstr=dstr, what=what, extra=extra)

    log(msg)
    init_sl_timer(th_name)

    return True


def init_sl_timer(th_name='DEFAULT'):
    """Initialises the timer for the step_log function"""
    with lock:
        sl_time_dict[th_name] = time()
