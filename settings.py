# -*-coding: utf-8 -*-
# Created by huangqiyin

import os
import yaml
import codecs

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = {}
with codecs.open(os.path.join(BASE_DIR, "settings.yaml"), mode='rb', encoding="utf-8") as f:
    config.update(yaml.load(f))

LOG_LEVEL = 'DEBUG' if config['DEBUG'] else 'INFO'
# create log dir
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)


def common_handler(log_name, log_level=LOG_LEVEL):
    return {
        'class': 'logging.FileHandler',
        'filename': os.path.join(log_dir, '%s1.log' % log_name),
        'mode': 'a+',  # todo must append mode
        'formatter': 'detailed',
        "encoding": 'utf-8',
        'level': log_level,
    }


config['logging'] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': "%(asctime)s [%(levelname)s] pid [%(process)d] %(filename)s function %(funcName)s line %(lineno)s : %(message)s",
            'class': 'logging.Formatter'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': LOG_LEVEL,
        },
        'appconfigsrv': common_handler('appconfigsrv'),
        'oplog': common_handler('oplog'),
        'errors': common_handler('errors', "ERROR"),
    },
    'loggers': {
        'errors': {
            'handlers': ['errors']
        },
        'appconfigsrv': {
            'handlers': ['appconfigsrv']
        },
        'oplog': {
            'handlers': ['oplog']
        },
    },
    'root': {
        'level': LOG_LEVEL,
        'handlers': ['console', 'errors', 'appconfigsrv'] if config['DEBUG'] else ['errors', 'appconfigsrv']
    },
}
