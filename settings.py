from os.path import isfile
from envparse import env

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


STATUS = {
	'OK': 1,
	'ERROR': 2,
	'INFO': 3,
	'UPDATE_USERS': 4
}
