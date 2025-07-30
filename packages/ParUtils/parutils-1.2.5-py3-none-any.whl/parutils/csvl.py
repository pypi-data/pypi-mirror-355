import csv
from io import TextIOWrapper

from . import file

SEPARATOR = ';'
E_WRONG_TYPE_LIST = "List elements must be of type list (if you want to save a list of strings, please use the save_list function)"


def get_csv_fields_dict(in_path):
    """Returns a dictionary whose keys are the CSV fields of the 'in_path' file
    and elements are the columns index.
    """

    fields = {}
    line_list = get_header(in_path, True)
    for i, elt in enumerate(line_list):
        fields[elt] = i

    return fields


def load_csv(in_path, quote=False):
    """Loads a CSV file and returns a list whose elements correspond to the
    lines of the 'in_path' file.
    Each element is also a list whose elements correspond to the CSV fields.
    When quote is True, the builtin CSV package is used and separators between quote char
    are ignored (less performant).
    """

    out_list = []
    with open(in_path, 'r', encoding='utf-8') as in_file:
        if quote:
            reader = csv.reader(in_file, delimiter=SEPARATOR, doublequote='"')
            for row in reader:
                out_list.append(row)
        else:
            for line in in_file:
                line_list = csv_to_list(line)
                out_list.append(line_list)

    return out_list


def csv_to_list(line_in: str):
    """Converts a CSV line to a list using SEPARATOR as separator"""

    return line_in.strip('\n').split(SEPARATOR)


def save_csv(array_in, out_path, mode='w', quote=False):
    """Saves a list to a CSV file

    - mode: mode for the open methode.
    - quote: determines whether each field should be wrapped in double quotes or not (default=False)
    """
    import os.path as p

    file.mkdirs(p.dirname(out_path))
    with open(out_path, mode, encoding='utf-8') as out_file:
        for row in array_in:
            write_csv_line(row, out_file, quote)


def write_csv_line(row, out_file: TextIOWrapper, quote=False):
    """Writes a line to a CSV file

    - row: must be a list
    """

    if not isinstance(row, list):
        raise Exception(E_WRONG_TYPE_LIST)
    if quote:
        row = [f'"{e}"' for e in row]
    line_out = SEPARATOR.join(row)
    line_out += '\n'
    out_file.write(line_out)


def csv_clean(s: str):
    """Cleans a CSV field by removing CSV separators and new line characters"""

    out = s.replace('\r', '')
    out = out.replace('\n', '')
    out = out.replace(SEPARATOR, '')
    return out


def get_header(in_path, csv=False):
    """Returns the header of a file

    - csv: if True, the returned header is a list containing each CSV field
    """

    with open(in_path, 'r', encoding='utf-8') as in_file:
        header = in_file.readline().strip('\n')

    if csv:
        header = csv_to_list(header)

    return header
