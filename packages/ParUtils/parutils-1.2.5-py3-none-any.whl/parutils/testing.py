from .strg import like
from .logging import log


def ttry(f, e_ref, *args, **kwargs):

    exception_occured = False
    try:
        f(*args, **kwargs)
    except Exception as e:
        exception_occured = True
        if like(str(e), e_ref):
            log(f"[ttry] Exception caught match expected ('{e_ref}')")
        else:
            s = f"[ttry] Exception caught ('{str(e)}') don't match expected ('{e_ref}')"
            log(s)
            raise Exception(s)

    if not exception_occured:
        s = "[ttry] No exception was caught"
        log(s)
        raise Exception(s)
