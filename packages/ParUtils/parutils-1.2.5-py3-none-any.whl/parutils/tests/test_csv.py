import parutils as u

IN1_PATH = 'parutils\\tests\\files\\in1.csv'
IN3_PATH = 'parutils\\tests\\files\\in3.csv'
OUT_PATH = 'parutils\\tests\\files\\out.csv'


def test_csv():

    ar1 = u.load_csv(IN3_PATH, True)
    assert ar1[1][1] == 'comment1;comment2'
    u.save_csv(ar1, IN3_PATH, quote=True)
    ar2 = u.load_csv(IN3_PATH, True)
    assert ar1 == ar2

    d = u.get_csv_fields_dict(IN1_PATH)
    assert d == {'ID': 0, 'NAME': 1}

    s = u.csv_clean('FIELD1;\n')
    assert s == 'FIELD1'

    e_ref = u.csvl.E_WRONG_TYPE_LIST
    u.ttry(u.save_csv, e_ref, ['1'], OUT_PATH)


if __name__ == '__main__':  # pragma: no cover
    test_csv()
