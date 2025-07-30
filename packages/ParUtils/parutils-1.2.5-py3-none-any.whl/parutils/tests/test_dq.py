import parutils.tests.conftest as conftest
import parutils as u

FILES_DIR = 'parutils\\tests\\files'
OUT_DIR = conftest.TESTS_OUT_DIR
DUP_IN = FILES_DIR + '\\dup_in.csv'
DUP_OUT = OUT_DIR + '\\out_dup.csv'
DUP_OUT_REF = FILES_DIR + '\\dup_out_ref.csv'
IN_1 = FILES_DIR + '\\in1.csv'
IN_2 = FILES_DIR + '\\in2.csv'


def test_dq():

    u.Logger('TEST_DQ', True)
    u.log_print("Test toolDup - find_dup_list", dashes=100)
    list_in = u.load_csv(DUP_IN)
    dup_list = u.find_dup_list(list_in)
    u.log_example(dup_list)
    u.save_csv(dup_list, DUP_OUT)
    u.file_match(DUP_OUT, DUP_OUT_REF, del_dup=True)
    u.diff_list(['1'], ['2'])

    e_ref = "Files don't match"
    u.ttry(u.file_match, e_ref, IN_1, IN_2)

    assert u.find_dup_list([]) == []
    assert u.del_dup_list([]) == []
    u.close_logger()


if __name__ == '__main__':  # pragma: no cover
    from parutils.tests.conftest import init
    init()
    test_dq()
