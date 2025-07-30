import os.path as p
import parutils as u

from . import wrap

OUT_DIR = 'out'


@wrap.simple
def file_match(in1, in2, del_dup=False, err=True, out_path=''):
    """Compares two files and outputs the diff if the files don't match.
    Note that the files are sorted before comparison.

    - del_dup: if true, duplicates are deleted before comparison
    - err: if True, an exception is raised when the files don't match
    - out_path: specifies an output path for file comparison different from default
    """

    s = f"Comparing files '{in1}' and '{in2}'..."
    u.log(s)
    l1, l2 = u.load_txt(in1), u.load_txt(in2)
    l1.sort(), l2.sort()
    if del_dup:
        l1, l2 = del_dup_list(l1), del_dup_list(l2)

    res = l1 == l2
    s = "Files match" if res else "Files don't match"
    u.log(s)

    if not res:
        diff_list(l1, l2, out_path)
        if err:
            raise Exception(s)


def diff_list(list1, list2, out_path=''):

    if not out_path:
        u.mkdirs(OUT_DIR)
        out_path = p.join(OUT_DIR, 'file_match_out.csv')

    out1 = [e for e in list1 if e not in list2]
    out2 = [e for e in list2 if e not in list1]
    out = del_dup_list(out1 + out2)
    u.save_list(out, out_path)
    u.log(f"Comparison result available here: {out_path}")


def find_dup_list(in_list):
    """Returns a list of the duplicates in in_list"""

    if not in_list:
        return []

    in_sorted = sorted(in_list)
    dup_list = []
    old_elt = in_sorted[0]
    for elt in in_sorted[1:]:
        if elt == old_elt:
            dup_list.append(elt)
        else:
            old_elt = elt

    if dup_list:
        dup_list = del_dup_list(dup_list)

    return dup_list


def del_dup_list(in_list):
    """Returns in_list sorted and without duplicates"""

    if not in_list:
        return []

    # If in_list elements are hashable
    if isinstance(in_list[0], str):
        out_list = list(set(in_list))
        out_list.sort()
        return out_list

    # If not
    in_sorted = sorted(in_list)
    out_list = [in_sorted[0]]
    old_elt = in_sorted[0]
    for elt in in_sorted[1:]:
        if elt > old_elt:
            out_list.append(elt)
            old_elt = elt

    return out_list
