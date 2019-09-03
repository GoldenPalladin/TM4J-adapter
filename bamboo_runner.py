"""
Module takes script name as argument, updates config parameter values
from file bamboo_env_file and runs required script
"""
from os import path, system
import configparser
import re
import logging
import argparse
from files import do

logging.basicConfig(level=logging.INFO)


def is_config_variable(key: str) -> bool:
    """
    Check if the string matches config option pattern
    :param key: string to be checked
    :return: bool
    """
    return bool(re.search(r'(GENERAL|NOTFOUND|BDD|RESULTS|JUNIT|JSON|LOGGING)_([a-z]+(?:_[a-z]+)*)', key))


def split_option(file_obj) -> dict:
    """
    Function splits file contents in format key=value into
    {key:value} dict
    :param file_obj:
    :return: dict
    """
    return dict(item.split("=") for item in file_obj.readlines())


def main():
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option  # overriding to aviod lowercasing the options
    do('parseconfig.ini', 'r', config.read_file)
    bb_variables = do('bamboo_env_file', 'r', split_option)
    for (k, v) in bb_variables.items():
        key = k.strip('bamboo_')
        if is_config_variable(key):
            option = key.split('_')
            try:
                if config.has_option(option[0], option[1]):
                    config.set(option[0], option[1], v)
                    logging.info(f'Updated config parameter: [{option[0]}][{option[1]}] = {v}')
                else:
                    logging.error(f'No [{option[1]}] option found in [{option[0]}] section of parseconfig.ini file')
            except configparser.NoSectionError:
                logging.error(f'No [{option[0]}] section found in parseconfig.ini file')
    do('parseconfig.ini', 'w', config.write)
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--script", help="Script name to run")
    args = parser.parse_args()
    script = path.join(path.abspath(path.dirname(__file__)), f'{args.script}.py')
    logging.info(f'Executing script {script}')
    system(f'python {script}')


if __name__ == '__main__':
    main()
