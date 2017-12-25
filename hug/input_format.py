"""hug/input_formats.py

Defines the built-in Hug input_formatting handlers

Copyright (C) 2016  Timothy Edmund Crosley

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
from __future__ import absolute_import

import ujson as json_converter
from urllib.parse import parse_qs
from cgi import parse_header

from sanic.request import RequestParameters, parse_multipart_form
from hug.format import content_type, underscore


@content_type('text/plain')
async def text(body, charset='utf-8', **kwargs):
    """Takes plain text data"""
    stream = await body.read()
    return stream.decode(charset)


@content_type('application/json')
async def json(body, charset='utf-8', **kwargs):
    """Takes JSON formatted data, converting it into native Python objects"""
    stream = await body.read()
    return json_converter.loads(stream.decode(charset))


def _underscore_dict(dictionary):
    new_dictionary = {}
    for key, value in dictionary.items():
        if isinstance(value, dict):
            value = _underscore_dict(value)
        if isinstance(key, str):
            key = underscore(key)
        new_dictionary[key] = value
    return new_dictionary


async def json_underscore(body, charset='utf-8', **kwargs):
    """Converts JSON formatted date to native Python objects.

    The keys in any JSON dict are transformed from camelcase to underscore separated words.
    """
    return _underscore_dict(await json(body, charset=charset))


@content_type('application/x-www-form-urlencoded')
async def urlencoded(body, charset='ascii', **kwargs):
    """Converts query strings into native Python objects"""
    stream = await body.read()
    return RequestParameters(
        parse_qs(stream.decode('utf-8')))


@content_type('multipart/form-data')  # get from post ()
async def multipart(body, **header_params):
    content_type, parameters = parse_header('multipart/form-data')
    boundary = parameters['boundary'].encode('utf-8')
    parsed_form, parsed_files = (
        parse_multipart_form(body, boundary))
    parsed_files.update(parsed_form)
    return parsed_files
