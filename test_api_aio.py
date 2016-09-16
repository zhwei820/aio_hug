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
import hug
from aiohttp import web, MsgType

api = hug.API(__name__)

@hug.post("/async_test", versions = '1')
async def async_test(request, response, aa):
    return {"code": 0, "message": "test ok!"}


@hug.get("/async_test", versions = '2')
async def async_test1(request, response, aa:hug.types.number):
    ''' doc for this end point
    '''
    return 'test'
    # return web.json_response({'hello': 'world'})   

print(dir(__hug__.http.serve()))

