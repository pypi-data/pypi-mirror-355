"""This module contains some general written io functions for the mcp framework

The common in these functions is that they can handle all of the following:
- default input,
- arguments given in yaml configuration and
- loop iterators
"""

import os
import tarfile
import zipfile
from typing import Any

import mcpf_core.core.routines as routines
import mcpf_core.func.constants as constants
from mcpf_core.core.decorators import with_default_arguments


def print_to_stdout(data: dict[str, Any]) -> dict[str, Any]:
    """
    It prints out the given content of 'data' to the standard out.

    Yaml args:
        'input':    it is either a string literal or a label in 'data' which identifies the input,
                    by default it is constants.DEFAULT_IO_DATA_LABEL
        'is_literal':
                    if it is True then the argument 'input' is a string literal,
                    which will be displayed on the standard output,
                    by default it is False

    Returns in data:
        'output':   it is a label in 'data' which identifies the output (the displayed text),
                    by default it is constants.DEFAULT_IO_DATA_LABEL
    """
    # general code part 2/1
    meta = routines.get_meta_data(data)

    # default_arguments_values
    arg = {"input": constants.DEFAULT_IO_DATA_LABEL, "output": constants.DEFAULT_IO_DATA_LABEL, "is_literal": False}
    # merging default values with current argument values
    if meta[constants.ARGUMENTS]:
        arg = arg | meta[constants.ARGUMENTS]
    # if the function part of a loop
    if routines.is_iterated_value_available():
        data[arg["input"]] = routines.pop_iterated_value()
    if arg["is_literal"]:
        print(arg["input"])
        data[arg["output"]] = arg["input"]
    elif data[arg["input"]] is not None:
        print(data[arg["input"]])
        data[arg["output"]] = data[arg["input"]]
    routines.set_meta_in_data(data, meta)
    return data


def list_dir(data: dict[str, Any]) -> dict[str, Any]:
    """
    It returns the content of the given directory in a list.
    Yaml args:
        'input_path':       a string containing a directory path, which will be listed,
                            by default it is the value identified with the label
                            constants.DEFAULT_IO_DATA_LABEL (if it is a string)
        'relative_path':    a bool value, if it is 'True' the given 'input_path' is a relative path
                            by default it is 'False'
        'only_file_names_return':   a bool value, if it is 'True' the content of the given directory
                                    is returned without its path,
                                    by default it is 'False'
        'output_for_iteration':     a bool value, if it is 'True' the output (list) of the function is registered
                                    for a subsequent loop,
                                    by default it is 'False'

    Returns in data:
        'output':   it is a label in 'data' which identifies the output
                    (a list containing the content of the given directory),
                    by default it is constants.DEFAULT_IO_DATA_LABEL
    """
    # general code part 2/1
    meta = routines.get_meta_data(data)

    # default_arguments_values
    default_input_path = "."
    if constants.DEFAULT_IO_DATA_LABEL in data and isinstance(data[constants.DEFAULT_IO_DATA_LABEL], str):
        default_input_path = data[constants.DEFAULT_IO_DATA_LABEL]
    arg = {
        "output": constants.DEFAULT_IO_DATA_LABEL,
        "input_path": default_input_path,
        "relative_path": False,
        "only_file_names_return": False,
        "output_for_iteration": False,
    }
    # merging default values with current argument values
    if meta[constants.ARGUMENTS]:
        arg = arg | meta[constants.ARGUMENTS]
    # if the function part of a loop
    if routines.is_iterated_value_available():
        arg["input_path"] = routines.pop_iterated_value()

    # specific code part
    if arg["relative_path"]:
        if arg["input_path"] != ".":
            arg["input_path"] = os.path.join(routines.get_current_input_dir(meta), arg["input_path"])
        else:
            arg["input_path"] = routines.get_current_input_dir(meta)
    data[arg["output"]] = []
    if os.path.isdir(arg["input_path"]):
        if len(os.listdir(arg["input_path"])) != 0:
            for file in os.listdir(arg["input_path"]):
                if arg["input_path"] != "." and not arg["only_file_names_return"]:
                    data[arg["output"]].append(os.path.join(arg["input_path"], file))
                else:
                    data[arg["output"]].append(file)
    if arg["output_for_iteration"]:
        list_dir_for_loop = data[arg["output"]].copy()
        routines.register_loop_iterator_list(list_dir_for_loop)
    routines.set_meta_in_data(data, meta)
    return data


def set_next_tmp_dir_as_input_dir(data: dict[str, Any]) -> dict[str, Any]:
    """
    the given input directory, output directory and temporary directories are stored in a list by the framework
    (first element: input dir, subsequent elements temp dirs and the last element is output dir).
    The function set the upcoming tmp/output dir to the default input dir
    """
    meta = routines.get_meta_data(data)
    routines.set_current_output_dir_to_input_dir(meta)
    routines.set_meta_in_data(data, meta)
    return data


def unzip(data: dict[str, Any]) -> dict[str, Any]:
    """
    It unzip the content of given input file/ dir.
    Yaml args:
        'input_path':       a string containing a directory path,
                            by default it is the value identified with the label
                            constants.DEFAULT_IO_DATA_LABEL (if it is a string)
        'relative_path':    a bool value, if it is 'True' the given 'input_path' is a relative path
                            by default it is 'False'
        'output_path':
        'file_name':
        'output_into_next_tmp_folder':

    Returns in data:
        'output':   it is a label in 'data' which identifies the output
                    (string describes the path to where the content of the file/dir was unzipped),
                    by default it is constants.DEFAULT_IO_DATA_LABEL
    """
    meta = routines.get_meta_data(data)
    # default_arguments_values
    default_input_path = "."
    if constants.DEFAULT_IO_DATA_LABEL in data and isinstance(data[constants.DEFAULT_IO_DATA_LABEL], str):
        default_input_path = data[constants.DEFAULT_IO_DATA_LABEL]
    arg = {
        "input_path": default_input_path,
        "output_path": ".",
        "output": constants.DEFAULT_IO_DATA_LABEL,
        "file_name": "",
        "relative_path": False,
        "output_into_next_tmp_folder": True,
    }
    # merging default values with current argument values
    if meta[constants.ARGUMENTS]:
        arg = arg | meta[constants.ARGUMENTS]
    # if the function part of a loop
    if routines.is_iterated_value_available():
        arg["input_path"] = routines.pop_iterated_value()

    # specific code part
    if arg["file_name"]:
        arg["input_path"] = os.path.join(arg["input_path"], arg["file_name"])

    if arg["relative_path"]:
        arg["input_path"] = os.path.join(routines.get_current_input_dir(meta), arg["input_path"])
    if arg["output_into_next_tmp_folder"]:
        arg["output_path"] = os.path.join(routines.get_current_tmp_dir(meta), arg["output_path"])

    if not os.path.exists(arg["output_path"]):
        os.makedirs(arg["output_path"])

    # Extract all files to the current directory
    if arg["input_path"][-3:].lower() == "zip":
        with zipfile.ZipFile(arg["input_path"], "r") as zip:
            zip.extractall(arg["output_path"])
    else:
        with tarfile.open(arg["input_path"], "r|*") as tar:
            tar.extractall(arg["output_path"])
    data[arg["output"]] = arg["output_path"]
    routines.set_meta_in_data(data, meta)
    return data


@with_default_arguments({"input": constants.DEFAULT_IO_DATA_LABEL, "output": constants.DEFAULT_IO_DATA_LABEL})
def extract_filename(data, has_iterated_value: bool, iterated_value: Any, arg: dict[str, Any]) -> dict[str, Any]:
    if has_iterated_value:
        arg["input"] = iterated_value
    if isinstance(data[arg["input"]], str):
        data[arg["output"]] = os.path.basename(data[arg["input"]])
    else:
        data[arg["output"]] = data[arg["input"]]

    return data


def set_default_file_name_from_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    It sets the given path to the default output file.
    Yaml args:
        'input':            a string containing a directory path,
                            by default it is the value identified with the label
                            constants.DEFAULT_IO_DATA_LABEL (if it is a string)

        'extension':    file extension can be given separately

    Returns in data:
        'output':   it is a label in 'data' which identifies the output
                    (the file path),
                    by default it is constants.DEFAULT_OUTPUT_FILE
    """
    # general code part 2/1
    meta = routines.get_meta_data(data)

    # default_arguments_values
    default_input = ""
    if constants.DEFAULT_IO_DATA_LABEL in data and isinstance(data[constants.DEFAULT_IO_DATA_LABEL], str):
        default_input = data[constants.DEFAULT_IO_DATA_LABEL]
    arg = {"input": default_input, "output": constants.DEFAULT_OUTPUT_FILE, "extension": ""}
    # merging default values with current argument values
    if meta[constants.ARGUMENTS]:
        arg = arg | meta[constants.ARGUMENTS]
    # if the function part of a loop
    if routines.is_iterated_value_available():
        arg["input"] = routines.pop_iterated_value()

    # specific code part
    data[arg["output"]] = data[arg["input"]] + arg["extension"]
    return data


def make_dir(data: dict[str, Any]) -> dict[str, Any]:
    """
    It creates the given directory, if it does not exist.
    Yaml args:
        'input_path':       a string containing a directory path, which will be created,
                            by default it is the value identified with the label
                            constants.DEFAULT_IO_DATA_LABEL (if it is a string)
        'relative_path':    a bool value, if it is 'True' the given 'input_path' is a relative path
                            by default it is 'False'

    Returns in data:
        'output':   it is a label in 'data' which identifies the output
                    (the absolute path of the created directory),
                    by default it is constants.DEFAULT_IO_DATA_LABEL
    """
    # general code part 2/1
    meta = routines.get_meta_data(data)

    # default_arguments_values
    default_input_path = "."
    if constants.DEFAULT_IO_DATA_LABEL in data and isinstance(data[constants.DEFAULT_IO_DATA_LABEL], str):
        default_input_path = data[constants.DEFAULT_IO_DATA_LABEL]
    arg = {"output": constants.DEFAULT_IO_DATA_LABEL, "input_path": default_input_path, "relative_path": False}
    # merging default values with current argument values
    if meta[constants.ARGUMENTS]:
        arg = arg | meta[constants.ARGUMENTS]
    # if the function part of a loop
    if routines.is_iterated_value_available():
        arg["input_path"] = routines.pop_iterated_value()

    # specific code part
    if arg["relative_path"]:
        if arg["input_path"] != ".":
            arg["input_path"] = os.path.join(routines.get_current_input_dir(meta), arg["input_path"])
        else:
            arg["input_path"] = routines.get_current_input_dir(meta)
    data[arg["output"]] = arg["input_path"]
    if not os.path.isdir(arg["input_path"]):
        os.makedirs(arg["input_path"])
    routines.set_meta_in_data(data, meta)
    return data


@with_default_arguments(
    {
        "input": constants.DEFAULT_IO_DATA_LABEL,
        "output": constants.DEFAULT_IO_DATA_LABEL,
        "is_input_literal": True,
        "is_new_value_literal": True,
        "label": "",
        "new_value": constants.DEFAULT_IO_DATA_LABEL,
        "may_new_value_come_from_loop": True,
    }
)
def substitute_str_in_str(data, has_iterated_value: bool, iterated_value: Any, arg: dict[str, Any]) -> dict[str, Any]:
    """
    Substitutes a placeholder in a string with a new value and updates the data dictionary with the result.

    Yaml args:
        - "input" (str): The key or literal string to use as the input string.
        - "new_value" (str): The key or literal string to use as the new value.
        - "may_new_value_come_from_loop" (bool): If True, use iterated_value as the new value; otherwise, as the input string.
        - "is_input_literal" (bool): If False, treat "input" as a key in data; otherwise, as a literal string.
        - "is_new_value_literal" (bool): If False, treat "new_value" as a key in data; otherwise, as a literal string.
        - "label" (str): The placeholder label to be replaced in the input string. Do not
                            include the curly braces in the label.
        - "output" (str): The key under which to store the result in data.

    Returns in data:
        - "output" (str): The key in data where the substituted string is stored.
                          If the input string is empty or None, it will be set to None.
    """
    input_string: str = arg["input"]
    new_value: str = arg["new_value"]
    if has_iterated_value:
        if arg["may_new_value_come_from_loop"]:
            new_value = iterated_value
        else:
            input_string = iterated_value

    if not arg["is_input_literal"]:
        input_string = data[input_string]
    if not arg["is_new_value_literal"]:
        new_value = data[new_value]

    if input_string and arg["label"]:
        data[arg["output"]] = input_string.replace("{" + arg["label"] + "}", new_value)
    else:
        data[arg["output"]] = None
    return data
