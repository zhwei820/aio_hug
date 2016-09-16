from os.path import isfile
from envparse import env
import logging

log = logging.getLogger('app')
log.setLevel(logging.DEBUG)

f = logging.Formatter('[L:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', datefmt = '%d-%m-%Y %H:%M:%S')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(f)
log.addHandler(ch)

if isfile('.env'):
    env.read_envfile('.env')

DEBUG = env.bool('DEBUG', default=False)

SITE_HOST = env.str('HOST')
SITE_PORT = env.int('PORT')
SECRET_KEY = env.str('SECRET_KEY')
MYSQL_HOST = env.str('MYSQL_HOST')
MYSQL_DB_NAME = env.str('MYSQL_DB_NAME')
MYSQL_USER = env.str('MYSQL_USER')
MYSQL_PASSWORD = env.str('MYSQL_PASSWORD')

PLAYERS_IN_GAME = 2

STATUS = {
	'OK': 1,
	'ERROR': 2,
	'INFO': 3,
	'UPDATE_USERS': 4
}

PONG_WS_INTERVAL = 60
DRAW = -1