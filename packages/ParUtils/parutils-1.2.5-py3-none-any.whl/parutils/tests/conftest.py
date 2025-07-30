TESTS_LOG_DIR = 'log\\tests'
TESTS_OUT_DIR = 'out\\tests'


def init():
    import parutils as u
    import parutils.logging.const as const

    const.DEFAULT_DIR = TESTS_LOG_DIR
    u.dq.OUT_DIR = TESTS_OUT_DIR
    u.mkdirs(TESTS_LOG_DIR, True)
    u.mkdirs(TESTS_OUT_DIR, True)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    init()
