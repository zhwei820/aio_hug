"""Simple 1 endpoint Fake HUG API module usable for testing importation of modules"""
import hug


class FakeSimpleException(Exception):
    pass

@hug.get()
async def made_up_hello():
    """for science!"""
    return 'hello'

@hug.get('/exception')
async def made_up_exception():
    raise FakeSimpleException('test')
