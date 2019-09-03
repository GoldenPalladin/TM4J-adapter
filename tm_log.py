"""
Module exports logging configuration
"""
import os
import configparser
from splunk_handler import SplunkHandler
import logging

config = configparser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'parseconfig.ini'))
log_config = config['LOGGING']


LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'consoleFormatter': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'csvFormatter': {
            'class': 'logging.Formatter',
            'format': '%(message)s'
        },
    },
    'handlers': {
        'splunk': {
            'level': 'INFO',
            'class': 'splunk_handler.SplunkHandler',
            'formatter': 'csvFormatter',
            'host': log_config['splunkHost'],
            'port': log_config['splunkPort'],
            'token': log_config['splunkToken'],
            'index': log_config['splunkIndex'],
            'sourcetype': 'json'
        },
        'console': {
            'level': 'NOTSET',
            'class': 'logging.StreamHandler',
            'formatter': 'consoleFormatter'
        },
        'csv': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'csvFormatter',
            'filename': log_config['logTcCreationPath']
        }
    },
    'loggers': {
        'tmconnect': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'tmconnectCSV': {
            'handlers': ['csv'],
            'level': 'INFO',
        },
        'tmconnectSplunk': {
            'handlers': ['splunk'],
            'level': 'INFO',
        },
        'junitParser': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'jsonParser': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'bddParser': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'postTestrun': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

