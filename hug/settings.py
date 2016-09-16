
import logging

log = logging.getLogger('qqqqapp')
log.setLevel(logging.DEBUG)

f = logging.Formatter('[L:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', datefmt = '%d-%m-%Y %H:%M:%S')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(f)
log.addHandler(ch)


HTTP_METHODS = ('call', 'cli', 'connect', 'delete', 'exception', 'get', 'get_post', 'head', 'http', 'local', 'not_found', 'object', 'options', 'patch', 'post', 'put', 'sink', 'static', 'trace')