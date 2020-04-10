"""
Module takes script name as argument, updates config parameter values
from file bamboo_env_file and runs required script
"""
from os import path, system
import configparser
import re
import argparse
from libs.files import do
from libs.tm_log import get_logger

logger = None


def is_config_variable(key: str) -> bool:
    """
    Check if the string matches config option pattern
    :param key: string to be checked
    :return: bool
    """
    return bool(re.search(r'(GENERAL|NOTFOUND|BDD|EXECUTION|ROCS|JUNIT|JSON|LOGGING)_([a-z]+(?:_[a-z]+)*)', key))


def split_option(file_obj) -> dict:
    """
    Function splits file contents in format key=value into
    {key:value} dict
    :param file_obj:
    :return: dict
    """
    result = list()
    for item in file_obj.readlines():
        if len(item.split("=")) == 2:
            result.append(item.split("="))
        else:
            logger.error(f'Cannot split&use string {item} properly: it must have name=value format')
    return {r[0]: r[1] for r in result}


def main():
    global logger
    try:
        config = configparser.ConfigParser()
        config.optionxform = lambda option: option  # overriding to aviod lowercasing the options
        do('parseconfig.ini', 'r', config.read_file)
        logger = get_logger(__name__, config)
        bb_variables = do('bamboo_env_file', 'r', split_option)
        for (k, v) in bb_variables.items():
            key = k.strip('bamboo_')
            if is_config_variable(key):
                option = key.split('_')
                try:
                    if config.has_option(option[0], option[1]):
                        config.set(option[0], option[1], v)
                        logger.info(f'Updated config parameter: [{option[0]}][{option[1]}] = {v}')
                    else:
                        logger.error(f'No [{option[1]}] option found in [{option[0]}] section of parseconfig.ini file')
                except configparser.NoSectionError:
                    logger.error(f'No [{option[0]}] section found in parseconfig.ini file')
        do('parseconfig.ini', 'w', config.write)
        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--script", help="Script name to run")
        args = parser.parse_known_args()
        script_file = path.join(path.abspath(path.dirname(__file__)), f'{args[0].script}.py')
        script_args = ' '.join(args[1])
        command = f'{script_file} {script_args}'
        logger.info(f'Executing script {command}')
        system(f'python {command}')
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
