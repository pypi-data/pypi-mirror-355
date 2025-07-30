import parutils as u
from parutils.tests.string.check_log import CL


def get_duration():
    u.log_print("Test get_duration_string", dashes=100)

    dstr = u.get_duration_string(0, end_time=0.35)
    u.log(dstr)
    assert dstr == "350 ms"

    (dms, dstr) = u.get_duration_string(0, end_time=5.369, return_dms=True)
    u.log(dstr, dms)
    assert (dstr, dms) == ("5.3 s", 5369)

    dstr = u.get_duration_string(0, end_time=150)
    u.log(dstr)
    assert dstr == "2 minutes and 30 seconds"

    u.log_print()


def like():
    u.log_print("Test of like functions", dashes=100)

    s = '2 test ok?'
    assert u.like(s, 'test')
    assert not u.like(s, 'test', exact=True)
    assert u.like(s, '*test*', exact=True)
    assert u.like(s, 'TEST', case_sensitive=False)
    assert u.like(s, 'TEST') is False
    u.log("like simple ok")

    m = u.like(s, '2 * ok?')
    assert m.group(1) == 'test'
    u.log("like m ok")

    lst = ['1', 'test']
    e_ref = u.strg.E_WRONG_TYPE_LIST
    u.ttry(u.like_list, e_ref, s, 'test')
    assert u.like_list(s, lst)
    assert u.like_list(s, lst, exact=True) is False
    assert u.like_list('TEST', lst) is False
    u.log("like_list ok")

    dct = {'1': ['a', 'b'], '2': 'test'}
    e_ref = u.strg.E_WRONG_TYPE_DICT
    u.ttry(u.like_dict, e_ref, s, 'test')
    assert u.like_dict(s, dct) == '2'
    assert u.like_dict(s, dct, exact=True) is False
    assert u.like_dict('b', dct) == '1'
    assert u.like_dict('TEST', dct) is False
    u.log("like_dict ok")

    assert u.hash512('TEST', 4) == '7bfa'
    assert len(u.gen_random_string(10)) == 10
    u.log_print()


def test_string():

    u.Logger('TEST_STRING', True)
    assert u.big_number(1000) == '1 000'
    assert u.truncate('test_test', 4) == 't...'
    get_duration()
    like()
    u.check_log(CL)
    u.close_logger()


if __name__ == '__main__':  # pragma: no cover
    from parutils.tests.conftest import init
    init()
    test_string()
