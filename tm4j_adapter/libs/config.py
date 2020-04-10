import configparser
from libs.files import try_file_exists


def read_config(config_path: str = None) -> configparser.ConfigParser:
    config_path = try_file_exists(file_path=config_path,
                                  default_path='parseconfig.ini',
                                  use_relative_path=True)
    if not _is_config_consistent(config_path):
        config_path = 'parseconfig.ini'
    c_config = configparser.ConfigParser()
    c_config.read(config_path)
    return c_config


def _is_config_consistent(config_path: str) -> bool:
    """
    Function checks if provided config has the same structure as 'parseconfig.ini' file
    :param config_path: path to config to check
    :return: True if config has all the sections and options as default
    """
    default_config = configparser.ConfigParser()
    custom_config = configparser.ConfigParser()
    default_config.read('parseconfig.ini')
    custom_config.read(config_path)
    for section in default_config.sections():
        for option in default_config[section]:
            if not custom_config.has_option(section, option):
                raise ValueError(f'Your config file is missing for {section}.{option} option')
    return True


config = read_config()
gen_config = config['GENERAL']
log_config = config['LOGGING']
not_config = config['NOTFOUND']
bdd_config = config['BDD']
jnt_config = config['JUNIT']
jsn_config = config['JSON']
exc_config = config['EXECUTION']

