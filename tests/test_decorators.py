"""tests/test_decorators.py.

Tests the decorators that power hugs core functionality

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
import json
import os
import sys
from unittest import mock

import sanic
import pytest
import requests

import hug

from .constants import BASE_DIRECTORY

api = hug.API(__name__)
module = sys.modules[__name__]

# Fix flake8 undefined names (F821)
__hug__ = __hug__  # noqa
__hug_wsgi__ = __hug_wsgi__  # noqa


@hug.http()
async def hello_world():
    return "Hello World!"


class API(object):
    @hug.call('/hello_world1')
    async def hello_world(self=None):
        return "Hello World!"


# class API1(object):  # todo
#     def __init__(self):
#         hug.call()(self.hello_world_method)

#     async def hello_world_method(self):
#         return "Hello World!"


@hug.call()
async def echo(text):
    return text


@hug.call(on_invalid=lambda data: 'error')
async def echo1(text):
    return text


def handle_error(data, request, response):
    return 'errored'


@hug.call(on_invalid=handle_error)
async def echo2(text):
    return text


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


@hug.call('/custom_route')
async def method_name():
    return 'works'


@hug.call()
async def multiple_parameter_types(start, middle: hug.types.text, end: hug.types.number = 5, **kwargs):
    return 'success'


@hug.get(raise_on_invalid=True)
async def my_handler(argument_1: int):
    return True


@hug.get(output=hug.output_format.png_image)
async def image():
    return 'artwork/logo.png'


@hug.get(parameters=('parameter1', 'parameter2'))
async def test_call(**kwargs):
    return kwargs


@pytest.fixture
def cli(loop, test_client):
    app = api.http.aio_server(loop)
    return loop.run_until_complete(test_client(app))


async def test_basic_call(cli):
    assert await hello_world() == "Hello World!"
    assert hello_world.interface.http

    resp = await cli.post('/hello_world')
    assert await resp.text() == '"Hello World!"'


async def test_basic_call_on_method(cli):
    """Test to ensure the most basic call still works if applied to a method"""

    api_instance = API()
    assert api_instance.hello_world.interface.http
    assert await api_instance.hello_world() == 'Hello World!'

    resp = await cli.post('/hello_world1')
    assert await resp.text() == '"Hello World!"'

    # api_instance = API1()
    # assert await api_instance.hello_world_method() == 'Hello World!'
    # resp = await cli.post('/hello_world_method')
    # assert await resp.text() == '"Hello World!"'


async def test_single_parameter(cli):
    """Test that an api with a single parameter interacts as desired"""

    assert await echo('Embrace') == 'Embrace'
    assert echo.interface.http
    with pytest.raises(TypeError):
        await echo()

    resp = await cli.get('/echo?text=Hello')
    assert await resp.text() == '"Hello"'

    resp = await cli.get('/echo')
    assert "required" in json.loads(await resp.text())['errors']['text'].lower()


async def test_on_invalid_transformer(cli):
    """Test to ensure it is possible to transform data when data is invalid"""

    resp = await cli.get('/echo1')
    assert await resp.text() == '"error"'

    resp = await cli.get('/echo2')
    assert await resp.text() == '"errored"'

    # resp = await cli.get('/echo')
    # assert "required" in json.loads(await
    # resp.text())['errors']['text'].lower()


# async def test_on_invalid_format(cli):  # todo
#     """Test to ensure it's possible to change the format based on a validation error"""

#     resp = await cli.get('/echo3?text=llll')
#     assert await resp.text() == '"error"'

# assert isinstance(hug.test.get(api, '/echo').data, dict)

# def smart_output_type(response, request):
#     if response and request:
#         return 'application/json'

# @hug.format.content_type(smart_output_type)
# def output_formatter(data, request, response):
# return hug.output_format.json((data, request and True, response and
# True))

# @hug.get(output_invalid=output_formatter, output=hug.output_format.file)
# def echo2(text):
#     return text

# assert isinstance(hug.test.get(api, '/echo2').data, (list, tuple))


#
# async def test_smart_route(cli):  # todo
#     """Test to ensure you can easily redirect to another method without an actual redirect"""
#
#     resp = await cli.get('/smart_route?implementation=1')
#     assert await resp.text() == '1'

# assert hug.test.get(api, 'smart_route', implementation=1).data == 1
# assert hug.test.get(api, 'smart_route', implementation=2).data == 2
# assert hug.test.get(api, 'smart_route', implementation=3).data == "NOT IMPLEMENTED"

async def test_custom_url(cli):
    """Test to ensure that it's possible to have a route that differs from the function name"""

    resp = await cli.get('/custom_route')
    assert await resp.text() == '"works"'

    resp = await cli.post('/custom_route')
    assert await resp.text() == '"works"'


# # def test_api_auto_initiate(): # not checked yet
# #     """Test to ensure that Hug automatically exposes a wsgi server method"""
# #     assert isinstance(__hug_wsgi__(create_environ('/non_existant'), StartResponseMock()), (list, tuple))

async def test_parameters(cli):
    """Tests to ensure that Hug can easily handle multiple parameters with multiple types"""

    resp = await cli.get('/multiple_parameter_types?start=start&middle=middle&end=7')
    assert await resp.text() == '"success"'

    resp = await cli.get('/multiple_parameter_types?start=start&middle=middle')
    assert await resp.text() == '"success"'

    resp = await cli.get('/multiple_parameter_types?start=start&middle=middle&other=7')
    assert await resp.text() == '"success"'

    resp = await cli.get('/multiple_parameter_types?start=start&middle=middle&end=nan')
    assert "end" in json.loads(await resp.text())['errors'].keys()


async def test_parameters(cli):
    """Tests to ensure that Hug can easily handle multiple parameters with multiple types"""

    resp = await cli.get('/multiple_parameter_types?start=start&middle=middle&end=7')
    assert await resp.text() == '"success"'


async def test_raise_on_invalid(cli):
    """Test to ensure hug correctly respects a request to allow validations errors to pass through as exceptions"""
    with pytest.raises(Exception):
        resp = await cli.get('/my_handler?argument_1=start')
        assert await resp.text() == '"success"'

    resp = await cli.get('/my_handler?argument_1=1')
    assert await resp.text() == 'true'


async def test_range_request(cli):
    """Test to ensure that requesting a range works as expected"""

    resp = await cli.get('/image', headers={'range': 'bytes=0-100'})


async def test_parameters_override(cli):
    """Test to ensure the parameters override is handled as expected"""

    resp = await cli.get('/test_call?parameter1=one&parameter2=two')
    assert json.loads(await resp.text()) == {"parameter1": "one",
                                             "parameter2": "two"}


@hug.call()
async def inject_request(request):
    return 'success'


@hug.call()
async def inject_response(response):
    return response and 'success'


@hug.call()
async def inject_both(request, response):
    return response and 'success'


@hug.call()
async def wont_appear_in_kwargs(**kwargs):
    return 'request' not in kwargs and 'response' not in kwargs and 'success'


async def test_parameter_injection(cli):
    """Tests that hug correctly auto injects variables such as request and response"""
    resp = await cli.get('/inject_request')
    assert await resp.text() == '"success"'

    resp = await cli.get('/inject_response')
    assert await resp.text() == '"success"'

    resp = await cli.get('/inject_both')
    assert await resp.text() == '"success"'

    resp = await cli.get('/wont_appear_in_kwargs')
    assert await resp.text() == '"success"'


@hug.get()
async def method_get():
    return 'GET'


@hug.post()
async def method_post():
    return 'POST'


@hug.connect()
async def method_connect():
    return 'CONNECT'


@hug.delete()
async def method_delete():
    return 'DELETE'


@hug.options()
async def method_options():
    return 'OPTIONS'


@hug.put()
async def method_put():
    return 'PUT'


@hug.trace()
async def method_trace():
    return 'TRACE'


@hug.call(accept=('GET', 'POST'))
async def accepts_get_and_post():
    return 'success'


async def test_method_routing(cli):
    """Test that all hugs HTTP routers correctly route methods to the correct handler"""

    resp = await cli.get('/method_get')
    assert await resp.text() == '"GET"'

    resp = await cli.post('/method_post')
    assert await resp.text() == '"POST"'

    # resp = await cli.connect('/method_connect')
    # assert await resp.text() == '"CONNECT"'
    # resp = await cli.trace('/method_trace')
    # assert await resp.text() == '"TRACE"'

    resp = await cli.delete('/method_delete')
    assert await resp.text() == '"DELETE"'

    resp = await cli.options('/method_options')
    assert await resp.text() == '"OPTIONS"'

    resp = await cli.put('/method_put')
    assert await resp.text() == '"PUT"'

    resp = await cli.get('/accepts_get_and_post')
    assert await resp.text() == '"success"'

    resp = await cli.post('/accepts_get_and_post')
    assert await resp.text() == '"success"'

    resp = await cli.put('/accepts_get_and_post')
    assert 'method not allowed' in (await resp.text()).lower()


@hug.not_found()
async def not_found_handler(response):
    response.set_status(404)  # todo
    return "Not Found"


async def test_not_found(cli):
    """Test to ensure the not_found decorator correctly routes 404s to the correct handler"""

    resp = await cli.post('/does_not_exist')
    assert await resp.text() == '"Not Found"'
    assert resp.status == 404

    resp = await cli.post('/v10/does_not_exist')
    assert await resp.text() == '"Not Found"'
    assert resp.status == 404


import tests.module_fake


@hug.extend_api()
def extend_with():
    return (tests.module_fake,)


async def test_not_found_with_extended_api(cli):
    """Test to ensure the not_found decorator works correctly when the API is extended"""
    resp = await cli.post('/v10/does_not_exist')
    assert await resp.text() == '"Not Found"'
    resp = await cli.get('/made_up_api')
    assert await resp.text() == '"made_up"'


@hug.get('/echo11')
async def echo11(text):
    return "Not version"


@hug.get('/echo11', versions=1)  # noqa
async def echo11(text):
    return text


@hug.get('/echo11', versions=range(2, 4))  # noqa
async def echo11(text):
    return "Echo: {text}".format(**locals())


@hug.get('/echo11', versions=7)  # noqa
async def echo11(text, api_version):
    return api_version


@hug.get('/echo11', versions=False)  # noqa
async def echo11(text):
    return "No Versions"


async def test_versioning(cli):
    """Ensure that Hug correctly routes API functions based on version"""

    resp = await cli.get('/v1/echo11?text=hi')
    assert await resp.text() == '"hi"'

    resp = await cli.get('/v2/echo11?text=hi')
    assert await resp.text() == '"Echo: hi"'

    resp = await cli.get('/v3/echo11?text=hi')
    assert await resp.text() == '"Echo: hi"'

    resp = await cli.get('/v4/echo11?text=hi')
    assert await resp.text() == '"Not Found"'

    resp = await cli.get('/echo11?text=hi')
    assert await resp.text() == '"Not version"'


@hug.get('/test_json')
async def a_test_json(text):
    return text


@hug.get('/test_json_body')
async def a_test_json_body(body):
    return body


@hug.get(parse_body=False)
async def a_test_json_body_stream_only(body=None):
    return body


async def test_json_auto_convert(cli):
    """Test to ensure all types of data correctly auto convert into json"""
    resp = await cli.get('/test_json?text=hi')
    assert await resp.text() == '"hi"'

    resp = await cli.get('/test_json_body')  # test
    assert await resp.read() == b'null'

    resp = await cli.get('/a_test_json_body_stream_only')
    assert await resp.text() == 'null'


@hug.get("/test_error")
async def a_test_error():
    return sanic.web.HTTPInternalServerError()
    # raise sanic.web.HTTPFound('/redirect')
    # return sanic.web.HTTPFound('/redirect')


async def test_error_handling(cli):
    """Test to ensure Hug correctly handles Falcon errors that are thrown during processing"""
    resp = await cli.get('/test_error')
    assert resp.status == 500


def raise_error(value):
    raise KeyError('Invalid value')


@hug.get('/test_error1')
async def b_test_error(data: raise_error):
    return True


async def test_error_handling_builtin_exception(cli):
    """Test to ensure built in exception types errors are handled as expected"""
    resp = await cli.get('/test_error1?data=1')
    assert resp.status == 400
    assert json.loads(await resp.text())['errors']['data'] == 'Invalid value'


@hug.get(output=hug.output_format.text)
async def stream_test():
    return open(os.path.join(BASE_DIRECTORY, 'README.md'), 'rb')


async def test_stream_return(cli):
    """Test to ensure that its valid for a hug API endpoint to return a stream"""
    resp = await cli.get('/stream_test')
    assert 'hug' in await resp.text()


def smart_output_type(response, request):
    if response and request:
        return 'application/json'


@hug.format.content_type(smart_output_type)
def output_formatter(data, request, response):
    return hug.output_format.json((data, request and True, response and True))


@hug.get(output=output_formatter)
async def output_test():
    return True


async def test_smart_outputter(cli):
    """Test to ensure that the output formatter can accept request and response arguments"""
    resp = await cli.get('/output_test')
    assert 'true' in await resp.text()


#
# @hug.default_output_format()
# def augmented(data):
#     return hug.output_format.json(['Augmented', data])


@hug.get(suffixes=('.js', '/js'), prefixes='/text')
async def hello101():
    return "world"


@pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
async def test_output_format(cli):
    """Test to ensure it's possible to quickly change the default hug output format"""
    old_formatter = api.http.output_format

    resp = await cli.get('/hello101')
    assert await resp.text() == '"world"'

    resp = await cli.get('/hello101.js')
    assert await resp.text() == '"world"'

    resp = await cli.get('/hello101/js')
    assert await resp.text() == '"world"'

    resp = await cli.get('/text/hello101')
    assert await resp.text() == '"world"'


@hug.request_middleware()
async def proccess_data(request):
    request.SERVER_NAME = 'Bacon'


# @hug.response_middleware()  # not understand
# def proccess_data2(request, response, resource):
#     response.set_header('Bacon', 'Yumm')


@hug.get()
async def hello545(request):
    return request.SERVER_NAME


@pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
async def test_middleware(cli):
    """Test to ensure the basic concept of a middleware works as expected"""
    resp = await cli.get('/hello545')
    assert await resp.text() == '"Bacon"'


def user_is_not_tim(request, response, **kwargs):
    if request.headers.get('USER', '') != 'Tim':
        return True
    return 'Unauthorized'


@hug.get(requires=user_is_not_tim)
async def hello_q(request):
    return 'Hi!'


async def test_requires(cli):
    """Test to ensure only if requirements successfully keep calls from happening"""

    resp = await cli.get('/hello_q')
    assert await resp.text() == '"Hi!"'

    resp = await cli.get('/hello_q', headers={'USER': 'Tim'})
    assert await resp.text() == '"Unauthorized"'


import tests.module_fake


@hug.extend_api('/aaa')
def extend_with():
    return (tests.module_fake,)


@hug.extend_api()
def extend_with():
    return (tests.module_fake,)


async def test_extending_api(cli):
    """Test to ensure it's possible to extend the current API from an external file"""
    resp = await cli.get('/made_up_api')
    assert await resp.text() == '"made_up"'

    resp = await cli.get('/aaa/made_up_api')
    assert await resp.text() == '"made_up"'


from tests.module_fake_simple import FakeSimpleException


@hug.exception(FakeSimpleException)
async def handle_exception(exception):
    return 'it works!'


@hug.extend_api('/fake_simple')
def extend_with():
    import tests.module_fake_simple
    return (tests.module_fake_simple,)


async def test_extending_api_with_exception_handler(cli):
    """Test to ensure it's possible to extend the current API from an external file"""
    resp = await cli.get('/fake_simple/exception')
    assert await resp.text() == '"it works!"'


@hug.extend_api('/fake', base_url='/api')
def extend_with():
    import tests.module_fake
    return (tests.module_fake,)


async def test_extending_api_with_base_url(cli):
    """Test to ensure it's possible to extend the current API with a specified base URL"""
    resp = await cli.get('/api/v1/fake/made_up_api')
    assert await resp.text() == '"made_up"'


@hug.get()
async def made_up_hello():
    return 'hi'


@hug.extend_api(base_url='/api')
def extend_with():
    import tests.module_fake_simple
    return (tests.module_fake_simple,)


async def test_extending_api_with_same_path_under_different_base_url(cli):
    """Test to ensure it's possible to extend the current API with the same path under a different base URL"""
    resp = await cli.get('/api/made_up_hello')
    assert await resp.text() == '"hello"'

    resp = await cli.get('/made_up_hello')
    assert await resp.text() == '"hi"'


@hug.get(response_headers={'name': 'Timothy'})
async def endpoint():
    return ''


@pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
async def test_adding_headers(cli):
    """Test to ensure it is possible to inject response headers based on only the URL route"""

    resp = await cli.get('/endpoint')
    assert await resp.text() == '""'
    assert resp.headers['name'] == 'Timothy'

# @pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
# def test_exceptions():    todo
#     """Test to ensure hug's exception handling decorator works as expected"""
#     @hug.get()
#     def endpoint():
#         raise ValueError('hi')

#     with pytest.raises(ValueError):
#         hug.test.get(api, 'endpoint')

#     @hug.exception()
#     def handle_exception(exception):
#         return 'it worked'

#     assert hug.test.get(api, 'endpoint').data == 'it worked'

#     @hug.exception(ValueError)  # noqa
#     def handle_exception(exception):
#         return 'more explicit handler also worked'

#     assert hug.test.get(api, 'endpoint').data == 'more explicit handler also worked'


# def test_error_handling_custom():  pass
#     """Test to ensure custom exceptions work as expected"""
#     class Error(Exception):

#         def __str__(self):
#             return 'Error'

#     def raise_error(value):
#         raise Error()

#     @hug.get()
#     def test_error(data: raise_error):
#         return True

#     response = hug.test.get(api, 'test_error', data=1)
#     assert 'errors' in response.data
#     assert response.data['errors']['data'] == 'Error'

# @pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
# def test_content_type_with_parameter():  // pass
#     """Test a Content-Type with parameter as `application/json charset=UTF-8`
#     as described in https://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.7"""
#     @hug.get()
#     def demo(body):
#         return body

#     assert hug.test.get(api, 'demo', body={}, headers={'content-type': 'application/json'}).data == {}
#     assert hug.test.get(api, 'demo', body={}, headers={'content-type': 'application/json; charset=UTF-8'}).data == {}


# @pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
# def test_validate():  // pass
#     """Test to ensure hug's secondary validation mechanism works as expected"""
#     def contains_either(fields):
#         if not 'one' in fields and not 'two' in fields:
#             return {'one': 'must be defined', 'two': 'must be defined'}

#     @hug.get(validate=contains_either)
#     def my_endpoint(one=None, two=None):
#         return True


#     assert hug.test.get(api, 'my_endpoint', one=True).data
#     assert hug.test.get(api, 'my_endpoint', two=True).data
#     assert hug.test.get(api, 'my_endpoint').status
#     assert hug.test.get(api, 'my_endpoint').data == {'errors': {'one': 'must be defined', 'two': 'must be defined'}}


# def test_urlencoded():  // pass
#     """Ensure that urlencoded input format works as intended"""
#     @hug.post()
#     def test_url_encoded_post(**kwargs):
#         return kwargs

#     test_data = b'foo=baz&foo=bar&name=John+Doe'
#     assert hug.test.post(api, 'test_url_encoded_post', body=test_data, headers={'content-type': 'application/x-www-form-urlencoded'}).data == {'name': 'John Doe', 'foo': ['baz', 'bar']}


# def test_multipart(): pass
#     """Ensure that multipart input format works as intended"""
#     @hug.post()
#     def test_multipart_post(**kwargs):
#         return kwargs

#     with open(os.path.join(BASE_DIRECTORY, 'artwork', 'logo.png'),'rb') as logo:
#         prepared_request = requests.Request('POST', 'http://localhost/', files={'logo': logo}).prepare()
#         logo.seek(0)
#         output = json.loads(hug.defaults.output_format({'logo': logo.read()}).decode('utf8'))
#         assert hug.test.post(api, 'test_multipart_post',  body=prepared_request.body,
#                              headers=prepared_request.headers).data == output


# def test_json_null(hug_api): pass
#     """Test to ensure passing in null within JSON will be seen as None and not allowed by text values"""
#     @hug_api.route.http.post()
#     def test_naive(argument_1):
#         return argument_1

#     assert hug.test.post(hug_api, 'test_naive', body='{"argument_1": null}',
# headers={'content-type': 'application/json'}).data == None


#     @hug_api.route.http.post()
#     def test_text_type(argument_1: hug.types.text):
#         return argument_1


#     assert 'errors' in hug.test.post(hug_api, 'test_text_type', body='{"argument_1": null}',
# headers={'content-type': 'application/json'}).data


# def test_204_with_no_body(hug_api):  #pass
#     """Test to ensure returning no body on a 204 statused endpoint works without issue"""
#     @hug_api.route.http.delete()
#     def test_route(response):
#         response.status = hug.HTTP_204
#         return

#     assert '204' in hug.test.delete(hug_api, 'test_route').status


##########################################################################


# def test_return_modifer():
#     """Ensures you can modify the output of a HUG API using -> annotation"""
#     @hug.get()
#     def hello() -> lambda data: "Hello {0}!".format(data):
#         return "world"

#     assert hug.test.get(api, 'hello').data == "Hello world!"
#     assert hello() == 'world'

#     @hug.get(transform=lambda data: "Goodbye {0}!".format(data))
#     def hello() -> lambda data: "Hello {0}!".format(data):
#         return "world"
#     assert hug.test.get(api, 'hello').data == "Goodbye world!"
#     assert hello() == 'world'

#     @hug.get()
#     def hello() -> str:
#         return "world"
#     assert hug.test.get(api, 'hello').data == "world"
#     assert hello() == 'world'

#     @hug.get(transform=False)
#     def hello() -> lambda data: "Hello {0}!".format(data):
#         return "world"

#     assert hug.test.get(api, 'hello').data == "world"
#     assert hello() == 'world'

#     def transform_with_request_data(data, request, response):
#         return (data, request and True, response and True)

#     @hug.get(transform=transform_with_request_data)
#     def hello():
#         return "world"

#     response = hug.test.get(api, 'hello')
#     assert response.data == ['world', True, True]


# def test_marshmallow_support():
#     """Ensure that you can use Marshmallow style objects to control input and output validation and transformation"""
#     class MarshmallowStyleObject(object):
#         def dump(self, item):
#             return 'Dump Success'

#         def load(self, item):
#             return ('Load Success', None)

#         def loads(self, item):
#             return self.load(item)

#     schema = MarshmallowStyleObject()

#     @hug.get()
#     def test_marshmallow_style() -> schema:
#         return "world"

#     assert hug.test.get(api, 'test_marshmallow_style').data == "Dump Success"
#     assert test_marshmallow_style() == 'world'


#     @hug.get()
#     def test_marshmallow_input(item: schema):
#         return item

#     assert hug.test.get(api, 'test_marshmallow_input', item='bacon').data == "Load Success"
#     assert test_marshmallow_style() == 'world'

#     class MarshmallowStyleObjectWithError(object):
#         def dump(self, item):
#             return 'Dump Success'

#         def load(self, item):
#             return ('Load Success', {'type': 'invalid'})

#         def loads(self, item):
#             return self.load(item)

#     schema = MarshmallowStyleObjectWithError()

#     @hug.get()
#     def test_marshmallow_input2(item: schema):
#         return item

#     assert hug.test.get(api, 'test_marshmallow_input2', item='bacon').data == {'errors': {'item': {'type': 'invalid'}}}

#     class MarshmallowStyleField(object):
#         def deserialize(self, value):
#             return str(value)

#     @hug.get()
#     def test_marshmallow_input_field(item: MarshmallowStyleField()):
#         return item

#     assert hug.test.get(api, 'test_marshmallow_input_field', item='bacon').data == 'bacon'


# @hug.get(versions=(1, 2, None))
# async def my_api_function(hug_api_version):
#     return hug_api_version
#
# async def test_multiple_version_injection(cli):
#     """Test to ensure that the version injected sticks when calling other functions within an API"""
#     resp = await cli.get('/v1/my_api_function')
#     assert await resp.text() == '"1"'

#     assert hug.test.get(api, 'v1/my_api_function').data == 1
#     assert hug.test.get(api, 'v2/my_api_function').data == 2
#     assert hug.test.get(api, 'v3/my_api_function').data == 3

#     @hug.get(versions=(None, 1))
#     @hug.local(version=1)
#     def call_other_function(hug_current_api):
#         return hug_current_api.my_api_function()

#     assert hug.test.get(api, 'v1/call_other_function').data == 1
#     assert call_other_function() == 1

#     @hug.get(versions=1)
#     @hug.local(version=1)
#     def one_more_level_of_indirection(hug_current_api):
#         return hug_current_api.call_other_function()

#     assert hug.test.get(api, 'v1/one_more_level_of_indirection').data == 1
#     assert one_more_level_of_indirection() == 1

# @hug.default_output_format()
# def jsonify(data):
#     return hug.output_format.json(data)
#
# api.http.output_format = hug.output_format.text
#
# @hug.get()
# def my_method():
#     return {'Should': 'work'}
#
# assert hug.test.get(api, 'my_method').data == "{'Should': 'work'}"
# api.http.output_format = old_formatter

#
# @pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
# async def test_input_format(cli):
#     """Test to ensure it's possible to quickly change the default hug output format"""
#     old_format = api.http.input_format('application/json')
#     api.http.set_input_format('application/json', lambda a: {'no': 'relation'})
#
#     @hug.get()
#     def hello(body):
#         return body
#
#     assert hug.test.get(api, 'hello', body={'should': 'work'}).data == {'no': 'relation'}
#
#     @hug.get()
#     def hello2(body):
#         return body
#
#     assert not hug.test.get(api, 'hello2').data
#
#     api.http.set_input_format('application/json', old_format)


# @hug.static('/static')
# def my_static_dirs():
#     return (BASE_DIRECTORY, )
#
# async def test_static_file_support(cli):
#     """Test to ensure static file routing works as expected"""
#     resp = await cli.get('/static/README.md')
#     assert 'hug' in await resp.body()


# @hug.get()
# async def my_endpoint(hug_api):
#     return hug_api.http.not_found
#
#
# async def test_on_demand_404(cli):
#     """Test to ensure it's possible to route to a 404 response on demand"""
#     resp = await cli.get('/my_endpoint')
#     assert resp.status == 404


#     @hug.get()
#     def my_endpoint2(hug_api):
#         raise hug.HTTPNotFound()

#     assert '404' in hug.test.get(api, 'my_endpoint2').status

#     @hug.get()
#     def my_endpoint3(hug_api):
#         """Test to ensure base 404 handler works as expected"""
#         del hug_api.http._not_found
#         return hug_api.http.not_found

#     assert '404' in hug.test.get(api, 'my_endpoint3').status


# def test_output_format_inclusion(hug_api):
#     """Test to ensure output format can live in one api but apply to the other"""
#     @hug.get()
#     def my_endpoint():
#         return 'hello'

#     @hug.default_output_format(api=hug_api)
#     def mutated_json(data):
#         return hug.output_format.json({'mutated': data})

#     hug_api.extend(api, '')

#     assert hug.test.get(hug_api, 'my_endpoint').data == {'mutated': 'hello'}


# def test_cli():
#     """Test to ensure the CLI wrapper works as intended"""
#     @hug.cli('command', '1.0.0', output=str)
#     def cli_command(name: str, value: int):
#         return (name, value)

#     assert cli_command('Testing', 1) == ('Testing', 1)
#     assert hug.test.cli(cli_command, "Bob", 5) == ("Bob", 5)


# def test_cli_requires():
#     """Test to ensure your can add requirements to a CLI"""
#     def requires_fail(**kwargs):
#         return {'requirements': 'not met'}

#     @hug.cli(output=str, requires=requires_fail)
#     def cli_command(name: str, value: int):
#         return (name, value)

#     assert cli_command('Testing', 1) == ('Testing', 1)
#     assert hug.test.cli(cli_command, 'Testing', 1) == {'requirements': 'not met'}


# def test_cli_validation():
#     """Test to ensure your can add custom validation to a CLI"""
#     def contains_either(fields):
#         if not fields.get('name', '') and not fields.get('value', 0):
#             return {'name': 'must be defined', 'value': 'must be defined'}

#     @hug.cli(output=str, validate=contains_either)
#     def cli_command(name: str="", value: int=0):
#         return (name, value)

#     assert cli_command('Testing', 1) == ('Testing', 1)
#     assert hug.test.cli(cli_command) == {'name': 'must be defined', 'value': 'must be defined'}
#     assert hug.test.cli(cli_command, name='Testing') == ('Testing', 0)


# def test_cli_with_defaults():
#     """Test to ensure CLIs work correctly with default values"""
#     @hug.cli()
#     def happy(name: str, age: int, birthday: bool=False):
#         if birthday:
#             return "Happy {age} birthday {name}!".format(**locals())
#         else:
#             return "{name} is {age} years old".format(**locals())

#     assert happy('Hug', 1) == "Hug is 1 years old"
#     assert happy('Hug', 1, True) == "Happy 1 birthday Hug!"
#     assert hug.test.cli(happy, "Bob", 5) == "Bob is 5 years old"
#     assert hug.test.cli(happy, "Bob", 5, birthday=True) == "Happy 5 birthday Bob!"


# def test_cli_with_hug_types():
#     """Test to ensure CLIs work as expected when using hug types"""
#     @hug.cli()
#     def happy(name: hug.types.text, age: hug.types.number, birthday: hug.types.boolean=False):
#         if birthday:
#             return "Happy {age} birthday {name}!".format(**locals())
#         else:
#             return "{name} is {age} years old".format(**locals())

#     assert happy('Hug', 1) == "Hug is 1 years old"
#     assert happy('Hug', 1, True) == "Happy 1 birthday Hug!"
#     assert hug.test.cli(happy, "Bob", 5) == "Bob is 5 years old"
#     assert hug.test.cli(happy, "Bob", 5, birthday=True) == "Happy 5 birthday Bob!"

#     @hug.cli()
#     def succeed(success: hug.types.smart_boolean=False):
#         if success:
#             return 'Yes!'
#         else:
#             return 'No :('

#     assert hug.test.cli(succeed) == 'No :('
#     assert hug.test.cli(succeed, success=True) == 'Yes!'
#     assert 'succeed' in str(__hug__.cli)

#     @hug.cli()
#     def succeed(success: hug.types.smart_boolean=True):
#         if success:
#             return 'Yes!'
#         else:
#             return 'No :('

#     assert hug.test.cli(succeed) == 'Yes!'
#     assert hug.test.cli(succeed, success='false') == 'No :('

#     @hug.cli()
#     def all_the(types: hug.types.multiple=[]):
#         return types or ['nothing_here']

#     assert hug.test.cli(all_the) == ['nothing_here']
#     assert hug.test.cli(all_the, types=('one', 'two', 'three')) == ['one', 'two', 'three']

#     @hug.cli()
#     def all_the(types: hug.types.multiple):
#         return types or ['nothing_here']

#     assert hug.test.cli(all_the) == ['nothing_here']
#     assert hug.test.cli(all_the, 'one', 'two', 'three') == ['one', 'two', 'three']

#     @hug.cli()
#     def one_of(value: hug.types.one_of(['one', 'two'])='one'):
#         return value

#     assert hug.test.cli(one_of, value='one') == 'one'
#     assert hug.test.cli(one_of, value='two') == 'two'


# def test_cli_with_conflicting_short_options():
#     """Test to ensure that it's possible to expose a CLI with the same first few letters in option"""
#     @hug.cli()
#     def test(abe1="Value", abe2="Value2", helper=None):
#         return (abe1, abe2)

#     assert test() == ('Value', 'Value2')
#     assert test('hi', 'there') == ('hi', 'there')
#     assert hug.test.cli(test) == ('Value', 'Value2')
#     assert hug.test.cli(test, abe1='hi', abe2='there') == ('hi', 'there')


# def test_cli_with_directives():
#     """Test to ensure it's possible to use directives with hug CLIs"""
#     @hug.cli()
#     @hug.local()
#     def test(hug_timer):
#         return float(hug_timer)

#     assert isinstance(test(), float)
#     assert test(hug_timer=4) == 4
#     assert isinstance(hug.test.cli(test), float)


# def test_cli_with_named_directives():
#     """Test to ensure you can pass named directives into the cli"""
#     @hug.cli()
#     @hug.local()
#     def test(timer: hug.directives.Timer):
#         return float(timer)

#     assert isinstance(test(), float)
#     assert test(timer=4) == 4
#     assert isinstance(hug.test.cli(test), float)


# def test_cli_with_output_transform():
#     """Test to ensure it's possible to use output transforms with hug CLIs"""
#     @hug.cli()
#     def test() -> int:
#         return '5'

#     assert isinstance(test(), str)
#     assert isinstance(hug.test.cli(test), int)


#     @hug.cli(transform=int)
#     def test():
#         return '5'

#     assert isinstance(test(), str)
#     assert isinstance(hug.test.cli(test), int)


# def test_cli_with_short_short_options():
#     """Test to ensure that it's possible to expose a CLI with 2 very short and similar options"""
#     @hug.cli()
#     def test(a1="Value", a2="Value2"):
#         return (a1, a2)

#     assert test() == ('Value', 'Value2')
#     assert test('hi', 'there') == ('hi', 'there')
#     assert hug.test.cli(test) == ('Value', 'Value2')
#     assert hug.test.cli(test, a1='hi', a2='there') == ('hi', 'there')


# def test_cli_file_return():
#     """Test to ensure that its possible to return a file stream from a CLI"""
#     @hug.cli()
#     def test():
#         return open(os.path.join(BASE_DIRECTORY, 'README.md'), 'rb')

#     assert 'hug' in hug.test.cli(test)


# def test_local_type_annotation():
#     """Test to ensure local type annotation works as expected"""
#     @hug.local(raise_on_invalid=True)
#     def test(number: int):
#         return number

#     assert test(3) == 3
#     with pytest.raises(Exception):
#         test('h')

#     @hug.local(raise_on_invalid=False)
#     def test(number: int):
#         return number

#     assert test('h')['errors']

#     @hug.local(raise_on_invalid=False, validate=False)
#     def test(number: int):
#         return number

#     assert test('h') == 'h'


# def test_local_transform():
#     """Test to ensure local type annotation works as expected"""
#     @hug.local(transform=str)
#     def test(number: int):
#         return number

#     assert test(3) == '3'


# def test_local_on_invalid():
#     """Test to ensure local type annotation works as expected"""
#     @hug.local(on_invalid=str)
#     def test(number: int):
#         return number

#     assert isinstance(test('h'), str)


# def test_local_requires():
#     """Test to ensure only if requirements successfully keep calls from happening locally"""
#     global_state = False

#     def requirement(**kwargs):
#         return global_state and 'Unauthorized'

#     @hug.local(requires=requirement)
#     def hello():
#         return 'Hi!'

#     assert hello() == 'Hi!'
#     global_state = True
#     assert hello() == 'Unauthorized'

# @pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
# def test_sink_support():
#     """Test to ensure sink URL routers work as expected"""
#     @hug.sink('/all')
#     def my_sink(request):
#         return request.path.replace('/all', '')

#     assert hug.test.get(api, '/all/the/things').data == '/the/things'

# @pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
# def test_sink_support_with_base_url():
#     """Test to ensure sink URL routers work when the API is extended with a specified base URL"""
#     @hug.extend_api('/fake', base_url='/api')
#     def extend_with():
#         import tests.module_fake
#         return (tests.module_fake, )

#     assert hug.test.get(api, '/api/fake/all/the/things').data == '/the/things'

# def test_cli_with_string_annotation():
#     """Test to ensure CLI's work correctly with string annotations"""
#     @hug.cli()
#     def test(value_1: 'The first value', value_2: 'The second value'=None):
#         return True

#     assert hug.test.cli(test, True)


# def test_cli_with_kargs():
#     """Test to ensure CLI's work correctly when taking kargs"""
#     @hug.cli()
#     def test(*values):
#         return values

#     assert test(1, 2, 3) == (1, 2, 3)
#     assert hug.test.cli(test, 1, 2, 3) == ('1', '2', '3')


# def test_cli_using_method():
#     """Test to ensure that attaching a cli to a class method works as expected"""
#     class API(object):

#         def __init__(self):
#             hug.cli()(self.hello_world_method)

#         def hello_world_method(self):
#             variable = 'Hello World!'
#             return variable

#     api_instance = API()
#     assert api_instance.hello_world_method() == 'Hello World!'
#     assert hug.test.cli(api_instance.hello_world_method) == 'Hello World!'
#     assert hug.test.cli(api_instance.hello_world_method, collect_output=False) is None


# def test_cli_with_nested_variables():
#     """Test to ensure that a cli containing multiple nested variables works correctly"""
#     @hug.cli()
#     def test(value_1=None, value_2=None):
#         return 'Hi!'

#     assert hug.test.cli(test) == 'Hi!'


# def test_cli_with_exception():
#     """Test to ensure that a cli with an exception is correctly handled"""
#     @hug.cli()
#     def test():
#         raise ValueError()
#         return 'Hi!'

#     assert hug.test.cli(test) != 'Hi!'


# @pytest.mark.skipif(sys.platform == 'win32', reason='Currently failing on Windows build')
# def test_wraps():
#     """Test to ensure you can safely apply decorators to hug endpoints by using @hug.wraps"""
#     def my_decorator(function):
#         @hug.wraps(function)
#         def decorated(*kargs, **kwargs):
#             kwargs['name'] = 'Timothy'
#             return function(*kargs, **kwargs)
#         return decorated

#     @hug.get()
#     @my_decorator
#     def what_is_my_name(hug_timer=None, name="Sam"):
#         return {'name': name, 'took': hug_timer}

#     result = hug.test.get(api, 'what_is_my_name').data
#     assert result['name'] == 'Timothy'
#     assert result['took']

#     def my_second_decorator(function):
#         @hug.wraps(function)
#         def decorated(*kargs, **kwargs):
#             kwargs['name'] = "Not telling"
#             return function(*kargs, **kwargs)
#         return decorated

#     @hug.get()
#     @my_decorator
#     @my_second_decorator
#     def what_is_my_name2(hug_timer=None, name="Sam"):
#         return {'name': name, 'took': hug_timer}

#     result = hug.test.get(api, 'what_is_my_name2').data
#     assert result['name'] == "Not telling"
#     assert result['took']

#     def my_decorator_with_request(function):
#         @hug.wraps(function)
#         def decorated(request, *kargs, **kwargs):
#             kwargs['has_request'] = bool(request)
#             return function(*kargs, **kwargs)
#         return decorated

#     @hug.get()
#     @my_decorator_with_request
#     def do_you_have_request(has_request=False):
#         return has_request

#     assert hug.test.get(api, 'do_you_have_request').data


# def test_cli_with_empty_return():
#     """Test to ensure that if you return None no data will be added to sys.stdout"""
#     @hug.cli()
#     def test_empty_return():
#         pass

#     assert not hug.test.cli(test_empty_return)


# def test_startup():
#     """Test to ensure hug startup decorators work as expected"""
#     @hug.startup()
#     def happens_on_startup(api):
#         pass

#     assert happens_on_startup in api.http.startup_handlers


# def test_cli_api(capsys):
#     """Ensure that the overall CLI Interface API works as expected"""
#     @hug.cli()
#     def my_cli_command():

#     with mock.patch('sys.argv', ['/bin/command', 'my_cli_command']):
#         __hug__.cli()
#         out, err = capsys.readouterr()
#         assert "Success!" in out

#     with mock.patch('sys.argv', []):
#         with pytest.raises(SystemExit):
#             __hug__.cli()


# def test_cli_api_return():
#     """Ensure returning from a CLI API works as expected"""
#     @hug.cli()
#     def my_cli_command():
#         return "Success!"

#     my_cli_command.interface.cli()
