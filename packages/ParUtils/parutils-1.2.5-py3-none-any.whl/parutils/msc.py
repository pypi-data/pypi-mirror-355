from typing import List


def list_to_dict(list_in: List[str], separator='='):
    """Transforms 'list_in' into a dictionary using the 'separator'"""

    out = {}
    for elt in list_in:
        e = elt.split(separator)
        key = e[0].strip()
        value = elt[elt.find(separator) + 1:].strip()
        out[key] = value
    return out


def replace_from_dict(str_in: str, dict_in, var_del='@@'):
    """Replaces the variables (delimited by '@@') in 'str_in' with values
    from 'dict_in'.

    Example:
    - replace_from_dict('Hello @@VAR@@', {'VAR': 'world'}) returns 'Hello world'
    """

    for key in dict_in:
        str_in = str_in.replace(var_del + key + var_del, str(dict_in[key]))
    return str_in
