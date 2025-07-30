import parutils as u


def test_file():
    u.mkdirs('')

    assert u.list_files('not exist') == []
    assert len(u.list_files('parutils\\tests')) > 1

    out = u.list_files('parutils\\tests', only_list=['test'], ignore_list=['file', 'msc', '0'])
    assert out == ['parutils\\tests\\conftest.py', 'parutils\\tests\\test_csv.py', 'parutils\\tests\\test_dq.py']

    out = u.list_files('parutils\\tests', only_list=['in*.csv'], ignore_list=['file', 'msc', 'init'], incl_root=False, walk=True)
    assert out == ['in1.csv', 'in2.csv', 'in3.csv']

    out = u.list_files('parutils\\tests', only_list=['test'], ignore_list=['file', 'msc', 'init', '0'], abspath=True)
    lst = ['c:\\*\\tests\\conftest.py', 'c:\\*\\tests\\test_csv.py', 'c:\\*\\tests\\test_dq.py']
    for elt in out:
        assert u.like_list(elt, lst, case_sensitive=False)

    path = 'out\\tests\\out.txt'
    u.save_list(out, path)
    assert u.count_lines(path) == 3


if __name__ == '__main__':  # pragma: no cover
    test_file()
