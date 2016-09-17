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
from hug.database import init_db
from settings import *


@hug.http()
async def hello_world():
    return "Hello World!"

class API(object):    
    @hug.call('/hello_world1')
    async def hello_world(self=None):
        return "Hello World!"

# class API1(object):  # todo 
#     def __init__(self):
#         hug.call('/hello_world_method')(self.hello_world_method)

#     async def hello_world_method(self):
#         return "Hello World!"

@hug.get(output_invalid=hug.output_format.json, output=hug.output_format.file)
async def echo3(text):
    return text


@hug.get()
async def implementation_1():
    return 1

@hug.get()
async def implementation_2():
    return 2

@hug.get()
async def smart_route(implementation: int):
    if implementation == 1:
        return implementation_1
    elif implementation == 2:
        return implementation_2
    else:
        return "NOT IMPLEMENTED"









@hug.post("/async_test", versions = '1')
async def async_test(request, response, aa):
    return {"code": 0, "message": "test ok!"}


@hug.get("/async_test", versions = '2')
async def async_test1(request, response, aa:hug.types.number, bb):
    ''' doc for this end point
    '''
    return 'test'
    # return web.json_response({'hello': 'world'})   

# if not DEBUG:
#     @hug.not_found()
#     async def not_found(request):
#         return {'Nothing': 'to see'}


app = __hug__.http.server()

async def _init_db(app):
    app.db = await init_db(
        host=MYSQL_HOST,
        db=MYSQL_DB_NAME,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        loop=loop
        )
    return app

loop = asyncio.get_event_loop()
app = loop.run_until_complete(_init_db(app))


if __name__ == '__main__':
    __hug__.http.serve()
