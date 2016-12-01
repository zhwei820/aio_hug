"""tests/test_api.py.

Tests to ensure the API object that stores the state of each individual hug endpoint works as expected

Copyright (C) 2016 Timothy Edmund Crosley

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

"""
import hug, asyncio
from aiohttp import web, MsgType
from settings import *

@hug.get("/ping")
async def ping(request):
    """
    Description end-point

    ---
    tags:
    -   user
    summary: Create user
    description: This can only be done by the logged in user.
    operationId: examples.api.api.createUser
    produces:
    -   application/json
    parameters:
    -   in: body
        name: body
        description: Created user object
        required: false
        schema:
        type: object
        properties:
            id:
            type: integer
            format: int64
            username:
            type:
                - "string"
                - "null"
            firstName:
            type: string
            lastName:
            type: string
            email:
            type: string
            password:
            type: string
            phone:
            type: string
            userStatus:
            type: integer
            format: int32
            description: User Status
    responses:
    "201":
        description: successful operation
    """
    return "pong"


async def hello():
    await asyncio.sleep(10)
    return "haha"

@hug.get("/hello")
async def hello_world():
    res = await hello()
    return res

class API(object):
    @hug.get('/hello_world1')
    async def hello_world(self=None):
        return "Hello World!"

@hug.get(output=hug.output_format.png_image)
async def image():
    return 'artwork/logo.png'

@hug.post("/async_test", versions = '1', examples="/async_test?aa=1")
async def async_test(request, response, aa):
    return {"code": 0, "message": "test ok!"}


@hug.get("/async_test", versions = '2')
async def async_test1(request, response, aa:hug.types.number, bb):
    return 'test'

@hug.post('/test_json_body', examples='"')
async def a_test_json_body(body):
    return body

import tests.module_fake
@hug.extend_api('/aaa')
def extend_with():
    return (tests.module_fake, )

@hug.request_middleware()
async def proccess_data(request):
    request.SERVER_NAME = 'Bacon'

def user_is_not_tim(request, response, **kwargs):
    if request.headers.get('USER', '') != 'Tim':
        return True
    return 'Unauthorized'

@hug.get(requires=user_is_not_tim)
async def hello_q(request):
    return 'Hi!'

from tests.module_fake_simple import FakeSimpleException

@hug.exception(FakeSimpleException)
async def handle_exception(exception):
    return 'it works!'

@hug.extend_api('/fake_simple')
def extend_with1():
    import tests.module_fake_simple
    return (tests.module_fake_simple, )

@hug.post()
async def test_url_encoded_post(**kwargs):
    return kwargs

@hug.post()
async def test_multipart_post(**kwargs):
    return kwargs

@hug.post()
async def test_naive(argument_1):
    return argument_1

@hug.delete()
async def test_route(response):
    response.set_status(204)
    return

def contains_either(fields):
    if not 'one' in fields and not 'two' in fields:
        return {'one': 'must be defined', 'two': 'must be defined'}

@hug.get(validate=contains_either)
async def my_endpoint1(one=None, two=None):
    return True

class Error(Exception):
    def __str__(self):
        return 'Error'

def raise_error(value):
    raise Error()

@hug.get()
async def test_error(data: raise_error):
    return True

if __name__ == '__main__':
    api = __hug__.http
    api.serve(8082)
