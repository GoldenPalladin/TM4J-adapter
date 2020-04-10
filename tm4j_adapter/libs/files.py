import configparser
from os import path, listdir, makedirs
from logging import _loggerClass

"""Library implement file operations"""


def make_csv_path(log_config: dict, gen_config: dict) -> str:
    """
    :param log_config: logging configuration section
    :param gen_config: general configuration section
    :return: path to csv-log file
    """
    core_folder = gen_config['tcFolder'].split('/')[0]
    if not path.exists(log_config['logTcCreationFolder']):
        makedirs(log_config['logTcCreationFolder'])
    return get_full_path(path.join(f"{log_config['logTcCreationFolder']}", f"{core_folder}.csv"))


def get_list_of_files(dir_name: str, extension: str, use_relative_path: bool = False) -> list:
    """Function returns list of full paths for every .extension file located in the directory
    class+
    """
    list_of_file = listdir(get_full_path(dir_name, use_relative_path))
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
    with open(get_full_path(file_name), mode) as file:
        return things_to_do(file)


def get_full_path(base_path: str, use_relative_path: bool = False, *nested_paths) -> str:
    """
    :param base_path: relative path from config.ini file
    :param use_relative_path: if False -- current workdir is appended to path
    :return: absolute path to object
    """
    result = path.join(path.abspath(path.dirname(path.dirname(__file__))), base_path) \
        if use_relative_path and (base_path is not None) else base_path
    if nested_paths:
        for nested_path in nested_paths:
            result = path.join(result, nested_path)
    return result


def try_file_exists(file_path: str, default_path: str, logger: _loggerClass = None,
                    use_relative_path: bool = False,
                    raise_exception: bool = False) -> str:
    """
    Checks if file exist and returns its path
    :param file_path: path to check
    :param default_path: default path to return
    :param logger: logger to throw error if file don't exists
    :param use_relative_path: option to construct paths
    :param raise_exception: raise FilenotFound exception
    :return: path to file or default file
    """
    full_path = get_full_path(file_path, use_relative_path)
    if full_path and path.isfile(full_path):
        return full_path
    elif raise_exception:
        raise FileNotFoundError(f'File not found for path {full_path}.')
    else:
        if logger:
            logger.error(f'File not found for path {full_path}. Using default {default_path} file')
        return get_full_path(default_path, use_relative_path)


def get_relative_path_from_root(path_name: str, bdd_config: dict, revert: bool = False, ext: str = '') -> str:
    root_folder = path.join(bdd_config['localRepoRoot'], bdd_config['featuresFolderInLocalRepository'])
    if revert:
        return path.join(root_folder, f'{path_name}.{ext}')
    else:
        return path.splitext(path.relpath(path_name, root_folder))[0]


def find_file_in_list_by_name(file_name: str, path_variants: list, bdd_config: dict, loose_search: bool = False) -> str:
    """
    Search for a file by name in list of files
    :param file_name: file name to search
    :param path_variants: list of paths to search in
    :param bdd_config: bdd section of config
    :return: path to required file
    """
    for file in path_variants:
        if (file_name == get_relative_path_from_root(file, bdd_config)) or \
                (loose_search and (file_name.replace('\\', '').replace('/', '') in file.replace('\\', '').replace('/', ''))):
            return file
    raise FileNotFoundError(f'No path was found for {file_name}')


class FilesHandler:
    def __init__(self, config: configparser.ConfigParser, path_name: str):
        if not path.exists(path_name):
            raise FileNotFoundError(f'File or folder not found for path {path_name}')
        self.config = config
        self.path = path_name
        self.isFolder = path.isdir(path_name)
        self.extension = ''
        self.result_list = []
        self.use_relative_path = config['GENERAL']['useRelativePath']

    def get_list_of_files(self, extension: str = None) -> list:
        """Function returns list of full paths for every .extension file located in the directory"""
        self.extension = extension
        if self.isFolder:
            dir_name = self.path
            list_of_file = listdir(get_full_path(dir_name, self.use_relative_path))
            for entry in list_of_file:
                self.path = path.join(dir_name, entry)
                if path.isdir(self.path):
                    self.result_list = self.result_list + self.get_list_of_files()
                else:
                    self.result_list.append(self.path)
        else:
            self.result_list.append(self.path)
        self.path = None  # path is proceeded and won't be used anymore
        if extension:
            return list(filter((lambda file: self.__is_required_file(file)), self.result_list))
        else:
            return self.result_list

    def __is_required_file(self, file_path: str) -> bool:
        """Check if file has required extensions"""
        file_name, file_extension = path.splitext(file_path)
        return file_extension == f'.{self.extension}'

    def get_bdd_file_paths(self):
        """
        method to form folder structure, feature path and link
        :return:
        """
        feature_folder = path.join(self.config["BDD"]["localRepoRoot"],
                                   self.config["BDD"]["featuresFolderInLocalRepository"])
        feature_path = path.relpath(self.path, get_full_path(feature_folder, True))
        feature_link = f'{self.config["BDD"]["repoLink"]}/{feature_path}'\
            .replace('\\', '/')
        feature_folder_name = path.dirname(feature_path).replace('\\', '/').replace(' ', '_')
        return feature_folder_name, feature_link