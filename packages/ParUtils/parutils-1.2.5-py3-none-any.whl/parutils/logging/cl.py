import warnings
import parutils as u

from . import Logger
from .main import log
from .main import log_print
from .core import get_logger


def check_log(in_list=[], in_list_not=[], log_matches=False, max_warn=0, name=''):
    """Checks whether the current log file contains the 'in_list' elements.
    If it doesn't, a warning is thrown.

    - log_matches: if True, the matches are printed out in the log file
    """

    s = ' ' + name if name else ''
    log(f'check_log{s}...')
    logger = get_logger()
    txt = load_txt(logger)

    n_w = 0
    n_w += check(in_list, txt, logger.log_path, log_matches)
    n_w += check_not(in_list_not, txt, logger.log_path)

    check_warn(n_w, max_warn, name)


def load_txt(logger: Logger):
    if not hasattr(logger, 'log_path'):
        s = 'No log file has been initialised. Initialise a log file by instanciating a logger object with Logger().'
        raise Exception(s)
    txt = u.load_txt(logger.log_path, False)
    return txt


def check(in_list, txt, log_path, log_matches):
    n_w = 0
    for elt in in_list:
        m = u.like(txt, elt)
        if not m:
            n_w += 1
            s = f"Expression '{elt}' couldn't be found in log file {log_path}"
            log(s, c_out=False)
            warnings.warn(s)
        elif str(m) != 'True' and log_matches:
            log_print('Expression matched:', m.group(0))
    return n_w


def check_not(in_list_not, txt, log_path):
    n_w = 0
    for elt in in_list_not:
        m = u.like(txt, elt)
        if m:
            n_w += 1
            s = f"Expression '{elt}' was found in log file {log_path}"
            log(s, c_out=False)
            warnings.warn(s)
    return n_w


def check_warn(n_w, max_warn, name):
    s = f' {name}' if name else ''
    if n_w == 0:
        log(f'check_log{s} ok')
    elif n_w <= max_warn:
        log(f'check_log{s} ended with {n_w} warnings')
    else:
        s = f'check_log{s} nok, too many warnings ({n_w} warnings)'
        log(s)
        raise Exception(s)
