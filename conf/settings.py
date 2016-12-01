from os.path import isfile
from envparse import env

if isfile('.env'):
    env.read_envfile('.env')

DEBUG = env.bool('DEBUG', default=False)

TOKEN_SECRET_KEY = env.str('TOKEN_SECRET_KEY')

SITE_HOST = env.str('HOST', default='127.0.0.1')
SITE_PORT = env.int('PORT', default=8701)

DATABASE_URL = env.str('DATABASE_URL', default='mysql://root:spwx@localhost:3306/pinax_mysite')
DATABASE_URL_r = env.str('DATABASE_URL_r', default='mysql://root:spwx@localhost:3306/pinax_mysite')  # 只读库

REDIS_URL = env.str('REDIS_URL', default=False)  # cluster
# REDIS_URL_1 = env.str('REDIS_URL_1', default=False)
# REDIS_URL_2 = env.str('REDIS_URL_2', default=False)
# REDIS_URL_3 = env.str('REDIS_URL_3', default=False)

# REDIS_URL = env.str('REDIS_URL', default=False)  # cluster

VERIFY_SMS_CHANNEL = env.json('VERIFY_SMS_CHANNEL') # help='根据包名确定推送中心的产品id'

STATUS = {
	'OK': 1,
	'ERROR': 2,
	'INFO': 3,
	'UPDATE_USERS': 4
}
