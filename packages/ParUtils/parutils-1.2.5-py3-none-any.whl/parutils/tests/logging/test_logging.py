import pytest
import parutils as u
from parutils.logging import const
from parutils.tests.logging import check_log as cl


def t_log_every():
    u.g.logs = []
    u.close_logger()
    u.Logger('TEST_LOG_EVERY', log_every=4)
    u.log("log_elt_1")
    assert u.g.logs == []
    u.check_log(in_list_not=["log_elt_1"], name='LOG_EVERY_1')

    u.log("log_elt_2")
    u.log("log_elt_3")
    u.log("log_elt_4")
    u.check_log(["log_elt_1", "log_elt_2", "log_elt_3", "log_elt_4", 'check_log LOG_EVERY_1 ok'])
    assert len(u.g.logs) == 2

    u.log("log_elt_5")
    logs_txt = u.load_txt(u.get_logger().log_path, False)
    assert "log_elt_5" not in logs_txt
    assert len(u.g.logs) == 2

    log_path = u.get_logger().log_path
    logs = u.load_txt(log_path)
    assert len(logs) == 14 
    logs0 = u.close_logger().logs
    assert "log_elt_5" in logs0[2]
    logs = u.load_txt(log_path)
    assert len(logs) == 17 
    logs_txt = u.load_txt(log_path, False)
    assert "log_elt_5" in logs_txt
    assert len(u.g.logs) == 3
    u.log_print()


def t_log_file():
    u.g.logs = []
    u.close_logger()
    u.log("This won't be logged in a file\n")
    e_ref = "No log file has been initialised"
    u.ttry(u.check_log, e_ref, cl.LOG_FILE)
    u.log_print()

    u.Logger('TEST_LOGGING_1')
    u.Logger()
    u.set_logger(u.get_logger())
    u.log("This will be logged", "in a file\n")
    u.get_logger().empty_log_every_buffer()
    u.check_log(cl.LOG_FILE, cl.LOG_FILE_NOT, log_matches=True, name='LOG_FILE')
    u.check_log(["Expression matched: Log file initialised (*)"], name='LOG_MTACHES')
    u.log_print()


def t_warn():
    with pytest.warns(UserWarning):  # disables the warnings
        u.check_log(cl.LOG_FILE_NOT, cl.LOG_FILE, name='LOG_FILE', max_warn=10)
    u.check_log(cl.WARN, name='WARN')
    u.log_print()


def t_input(monkeypatch):
    monkeypatch.setattr('builtins.input', mock_input)
    assert u.log_input("Test log input") == "user command"
    u.check_log(cl.LOG_INPUT, name='LOG_INPUT')
    u.log_print()


def t_update_logs():
    s = "test update_logs"
    logs = u.get_logs()
    logs.append(s)
    u.update_logs(logs)
    new_logs = u.get_logs()
    assert logs == new_logs
    u.check_log([s], name='UPDATE_LOGS')
    u.log_print()


def t_level_warn_err():
    u.Logger('TEST_LOGGING_2')
    u.log("This will be logged", "in a file\n")
    u.log("This won't be logged in a file\n", level=1)
    u.log_print("This won't be logged in a file\n", level=1)
    with pytest.warns(UserWarning):
        e_ref = f"check_log LOG_FILE nok, too many warnings ({cl.N_W} warnings)"
        u.ttry(u.check_log, e_ref, cl.LOG_FILE_NOT, cl.LOG_FILE, name='LOG_FILE')
    u.check_log(cl.LEVEL_WARN_ERR, name='LEVEL_WARN_ERR')
    u.log_print()


def t_step_log():
    out_list = []
    u.init_sl_timer()
    for i in range(1, 21):
        # time.sleep(0.05)  # simulates io / calculation
        out_list.append(i)
        u.step_log(i, 5, "elements appended")

    u.log_print('\nout_list:', out_list)
    u.log_example(out_list)
    u.log_example([])
    u.check_log(cl.STEP_LOG, name='STEP_LOG')
    u.log_print()


def t_log_dict():
    ssd = {'sskey1': 'value1', 'sskey2': 'value2'}
    sd = {'skey1': 'value1', 'skey2': ssd}
    d = {'key1': 'value1', 'key2': 'value2', 'key3': sd}
    u.log_dict(d, depth=2, tab_char='  ')
    u.log_dict(d, depth=2, tab_char='    ')
    u.log_dict(d, depth=2, tab_char='\t')
    u.check_log(cl.LOG_DICT, name='LOG_DICT')
    u.log_print()


def t_err_handling():
    # Error handling - normal case
    logger = u.get_logger()
    back = logger.log_path
    logger.log_path = ':.:.'
    u.log('test error handling normal 1')
    u.log('test error handling normal 2')
    logger.log_path = back
    u.log('test error handling normal 3')

    # Error handling - max limit reatched case
    const.MAX_ERR_COUNT = 2
    logger.log_path = ':.:.'
    u.log('test error handling max limit 1')
    u.log('test error handling max limit 2')
    u.log('test error handling max limit 3')
    u.log('test error handling max limit 4')
    logger.log_path = back
    logger.file_write = True
    logger.buffer = ''
    assert "test error handling max limit 4" in logger.logs[-1]
    assert "The number of logging errors in a row reached" in logger.logs[-2]
    u.check_log(cl.ERR_HANDLING, cl.ERR_HANDLING_NOT, name='ERR_HANDLING')
    u.log_print()


def test_logging(monkeypatch):
    t_log_every()
    t_log_file()
    t_warn()
    t_input(monkeypatch)
    t_update_logs()
    u.check_log(cl.END_1, name='END_1')
    u.close_logger()
    u.log_print()

    t_level_warn_err()
    t_step_log()
    t_log_dict()
    t_err_handling()
    assert "This won't be logged in a file" in u.g.logs[0]
    u.check_log(cl.END_2, name='END_2')
    u.close_logger()
    u.log_print()


def mock_input(txt):
    out = "user command"
    print(txt + out)
    return out


if __name__ == '__main__':  # pragma: no cover
    from parutils.tests.conftest import init
    from _pytest.monkeypatch import MonkeyPatch

    init()
    test_logging(MonkeyPatch())
