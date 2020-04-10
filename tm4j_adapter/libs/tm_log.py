"""
Module exports logging configuration
"""

import logging
from splunk_handler import SplunkHandler
from classes.SplunkFormatter import SplunkFormatter
import logging.config
from libs.files import make_csv_path
from libs.config import log_config, gen_config, exc_config


LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'csvFormatter': {
            'class': 'logging.Formatter',
            'format': '%(message)s'
        }
    },
    'handlers': {
        'csv': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'csvFormatter',
            'filename': make_csv_path(log_config, gen_config)
        }
    },
    'loggers': {
        'tmconnectCSV': {
            'handlers': ['csv'],
            'level': 'INFO'
        }
    }
}

logging.config.dictConfig(LOG_CONFIG)
csv_logger = logging.getLogger('tmconnectCSV')


def get_log_level(level: str = 'info') -> str:
    log_levels = {
        'info': 'INFO',
        'debug': 'DEBUG',
        'error': 'ERROR'
    }
    return log_levels.get(level.lower(), 'INFO')


def get_logger(name, config=None) -> logging.Logger:
    """
    function to get logger with extra settings from config
    :param config:
    :return:
    """
    l_log_config = config['LOGGING'] if config else log_config
    project = config['GENERAL']['tm4jProjectKey'] if config else gen_config['tm4jProjectKey']
    reporter = config['EXECUTION']['reporter'] if config else exc_config['reporter']
    l_log_level = get_log_level(l_log_config['configLevel'])

    console_formatter = logging.Formatter('-->  %(asctime)s - %(name)s - %(levelname)s %(funcName)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    error_log_handler = logging.FileHandler('logs/error.log')
    error_log_handler.setFormatter(console_formatter)
    error_log_handler.setLevel(logging.ERROR)

    splunk_formatter = SplunkFormatter(logging_app='tm4j_adapter',
                                       project=project,
                                       reporter=reporter)
    splunk_handler = SplunkHandler(host=log_config['splunkHost'],
                                   port=log_config['splunkPort'],
                                   token=log_config['splunkToken'],
                                   index=log_config['splunkIndex'],
                                   record_format=True,
                                   sourcetype='json',
                                   debug=False)
    splunk_handler.setFormatter(splunk_formatter)
    splunk_handler.setLevel(logging.INFO)

    logger = logging.getLogger(name)
    logger.addHandler(console_handler)
    logger.addHandler(error_log_handler)
    logger.addHandler(splunk_handler)
    logger.setLevel(l_log_level)
    return logger



