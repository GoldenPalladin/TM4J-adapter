from os import path, listdir
"""Library implement file operations"""


def get_list_of_files(dir_name: str, extension: str) -> list:
    """Function returns list of full paths for every .feature file located in the directory"""
    list_of_file = listdir(path.join(path.abspath(path.dirname(__file__)), dir_name))
    all_files = list()
    for entry in list_of_file:
        full_path = path.join(dir_name, entry)
        if path.isdir(full_path):
            all_files = all_files + get_list_of_files(full_path, extension)
        else:
            all_files.append(full_path)
    return list(filter((lambda file: is_required_file(file, extension)), all_files))


def is_required_file(file_path: str, extension: str) -> bool:
    """Check if file has required extensions"""
    file_name, file_extension = path.splitext(file_path)
    return file_extension == extension


def do(file_name: str, mode: str, things_to_do: callable):
    """
    Function opens file and calls a function on its content
    :param file_name: file name to deal
    :param mode: file open mode
    :param things_to_do: function to call on file contents
    :return:
    """
    with open(path.join(path.abspath(path.dirname(__file__)), file_name), mode) as file:
        return things_to_do(file)
