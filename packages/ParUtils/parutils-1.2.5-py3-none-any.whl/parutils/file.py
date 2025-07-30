import os
import os.path as p
from shutil import rmtree

from .logging import log
from .strg import like_list


def delete_folder(dir):
    """Deletes a folder and its content"""

    if p.exists(dir):
        rmtree(dir)
        log(f"Folder '{dir}' deleted")


def mkdirs(dir, delete=False):
    """Same as os.makedirs but:
    - Input can also be a path
    - With a 'delete' option which (if True) deletes the folder if it already exists."""

    if not dir:
        return

    if p.exists(dir) and not delete:
        return
    if p.exists(dir) and delete:
        delete_folder(dir)
    os.makedirs(dir)
    log(f"Folder '{dir}' created")


def list_files(in_dir,
               walk=False,
               incl_root=True,
               abspath=False,
               only_list=[],
               ignore_list=[]):
    """Lists the files of the 'in_dir' directory

    - incl_root: if True, the root directory is included in each path
    - walk: if True, the files of all the subdirectories are listed as well
    - only_list: list of wanted patterns. e.g. ['*.py'] (only these patterns will be output)
    - ignore_list: list of unwanted patterns. e.g. ['*.pyc'] (these patterns won't be output)
    """

    if not p.exists(in_dir):
        return []

    out = []
    for root, dir, files in os.walk(in_dir):
        for file in files:
            cur_path = file if not incl_root else p.join(root, file)
            cur_path = p.abspath(cur_path) if abspath else cur_path
            only = not only_list or like_list(file, only_list, case_sensitive=False)
            ignore = not like_list(file, ignore_list, case_sensitive=False)
            if only and ignore:
                out.append(cur_path)
        if not walk:
            break

    out.sort()
    return out


def load_txt(in_path, list_out=True):
    """Loads a text file

    - list_out: if True, a list is output, each element representing a line of the file. If False, a string is output.
    """

    with open(in_path, 'r', encoding='utf-8') as f:
        data = f.read()

    if list_out:
        return data.split('\n')
    else:
        return data


def save_list(in_list, out_path, mode='w'):
    """Saves a list in a file, each element representing a line"""

    mkdirs(p.dirname(out_path))
    with open(out_path, mode, encoding='utf-8') as out_file:
        for elt in in_list:
            s = str(elt) + '\n'
            out_file.write(s)


def count_lines(in_path):
    """Counts the number of lines of a file"""

    with open(in_path, 'r', encoding='utf-8') as in_file:
        i = 0
        for line in in_file:
            i += 1

    return i
