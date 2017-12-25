"""hug/interface.py

Defines the various interface hug provides to expose routes to functions

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

import argparse
import os
import sys
from collections import OrderedDict
from functools import lru_cache, partial, wraps

import sanic

import hug._empty as empty
import hug.api
import hug.output_format
import hug.types as types
from hug import introspect
from hug.exceptions import InvalidTypeData
from hug.format import parse_content_type
from hug.types import MarshmallowSchema, Multiple, OneOf, SmartBoolean, Text, text


class Interfaces(object):
    """Defines the per-function singleton applied to hugged functions defining common data needed by all interfaces"""

    def __init__(self, function):
        self.api = hug.api.from_object(function)
        self.spec = getattr(function, 'original', function)
        self.arguments = introspect.arguments(function)
        self._function = function

        self.is_coroutine = introspect.is_coroutine(self.spec)
        if self.is_coroutine:
            self.spec = getattr(self.spec, '__wrapped__', self.spec)

        self.takes_kargs = introspect.takes_kargs(self.spec)
        self.takes_kwargs = introspect.takes_kwargs(self.spec)

        self.parameters = introspect.arguments(self.spec, 1 if self.takes_kargs else 0)
        if self.takes_kargs:
            self.karg = self.parameters[-1]

        self.defaults = {}
        for index, default in enumerate(reversed(self.spec.__defaults__ or ())):
            self.defaults[self.parameters[-(index + 1)]] = default

        self.required = self.parameters[:-(len(self.spec.__defaults__ or ())) or None]
        if introspect.is_method(self.spec) or introspect.is_method(function):
            self.required = self.required[1:]
            self.parameters = self.parameters[1:]

        self.all_parameters = set(self.parameters)
        if self.spec is not function:
            self.all_parameters.update(self.arguments)

        self.transform = self.spec.__annotations__.get('return', None)
        self.directives = {}
        self.input_transformations = {}
        for name, transformer in self.spec.__annotations__.items():
            if isinstance(transformer, str):
                continue
            elif hasattr(transformer, 'directive'):
                self.directives[name] = transformer
                continue

            if hasattr(transformer, 'load'):
                transformer = MarshmallowSchema(transformer)
            elif hasattr(transformer, 'deserialize'):
                transformer = transformer.deserialize

            self.input_transformations[name] = transformer

    def __call__(__hug_internal_self, *args, **kwargs):
        """"Calls the wrapped function, uses __hug_internal_self incase self is passed in as a kwarg from the wrapper"""
        # if not __hug_internal_self.is_coroutine:
        return __hug_internal_self._function(*args, **kwargs)

        # return asyncio_call(__hug_internal_self._function, *args, **kwargs)


class Interface(object):
    """Defines the basic hug interface object, which is responsible for wrapping a user defined function and providing
       all the info requested in the function as well as the route

       A Interface object should be created for every kind of protocal hug supports
    """
    __slots__ = ('interface', '_api', 'defaults', 'parameters', 'required', '_outputs', 'on_invalid', 'requires',
                 'validate_function', 'transform', 'examples', 'output_doc', 'wrapped', 'directives', 'all_parameters',
                 'raise_on_invalid', 'invalid_outputs')

    def __init__(self, route, function):
        if route.get('api', None):
            self._api = route['api']
        if 'examples' in route:
            self.examples = route['examples']
        if not hasattr(function, 'interface'):
            function.__dict__['interface'] = Interfaces(function)

        self.interface = function.interface
        self.requires = route.get('requires', ())
        if 'validate' in route:
            self.validate_function = route['validate']
        if 'output_invalid' in route:
            self.invalid_outputs = route['output_invalid']

        if not 'parameters' in route:
            self.defaults = self.interface.defaults
            self.parameters = self.interface.parameters
            self.all_parameters = self.interface.all_parameters
            self.required = self.interface.required
        else:
            self.defaults = route.get('defaults', {})
            self.parameters = tuple(route['parameters'])
            self.all_parameters = set(route['parameters'])
            self.required = tuple([parameter for parameter in self.parameters if parameter not in self.defaults])

        if 'output' in route:
            self.outputs = route['output']

        self.transform = route.get('transform', None)
        if self.transform is None and not isinstance(self.interface.transform, (str, type(None))):
            self.transform = self.interface.transform

        if hasattr(self.transform, 'dump'):
            self.transform = self.transform.dump
            self.output_doc = self.transform.__doc__
        elif self.transform or self.interface.transform:
            output_doc = (self.transform or self.interface.transform)
            self.output_doc = output_doc if type(output_doc) is str else output_doc.__doc__

        self.raise_on_invalid = route.get('raise_on_invalid', False)
        if 'on_invalid' in route:
            self.on_invalid = route['on_invalid']
        elif self.transform:
            self.on_invalid = self.transform

        defined_directives = self.api.directives()
        used_directives = set(self.parameters).intersection(defined_directives)
        self.directives = {directive_name: defined_directives[directive_name] for directive_name in used_directives}
        self.directives.update(self.interface.directives)

    @property
    def api(self):
        return getattr(self, '_api', self.interface.api)

    @property
    def outputs(self):
        return getattr(self, '_outputs', None)

    @outputs.setter
    def outputs(self, outputs):
        self._outputs = outputs  # pragma: no cover - generally re-implemented by sub classes

    def validate(self, input_parameters):
        """Runs all set type transformers / validators against the provided input parameters and returns any errors"""
        errors = {}
        for key, type_handler in self.interface.input_transformations.items():
            if self.raise_on_invalid:
                if key in input_parameters:
                    input_parameters[key] = type_handler(input_parameters[key])
            else:
                try:
                    if key in input_parameters:
                        input_parameters[key] = type_handler(input_parameters[key])
                except InvalidTypeData as error:
                    errors[key] = error.reasons or str(error.message)
                except Exception as error:
                    if hasattr(error, 'args') and error.args:
                        errors[key] = error.args[0]
                    else:
                        errors[key] = str(error)

        for require in self.interface.required:
            if not require in input_parameters:
                errors[require] = "Required parameter '{}' not supplied".format(require)
        if not errors and getattr(self, 'validate_function', False):
            errors = self.validate_function(input_parameters)
        return errors

    def check_requirements(self, request=None, response=None):
        """Checks to see if all requirements set pass

           if all requirements pass nothing will be returned
           otherwise, the error reported will be returned
        """
        for requirement in self.requires:
            conclusion = requirement(response=response, request=request, module=self.api.module)
            if conclusion and conclusion is not True:
                return conclusion

    def documentation(self, add_to=None):
        """Produces general documentation for the interface"""
        doc = OrderedDict if add_to is None else add_to

        usage = self.interface.spec.__doc__
        if usage:
            doc['usage'] = usage
        if getattr(self, 'requires', None):
            doc['requires'] = [getattr(requirement, '__doc__', requirement.__name__) for requirement in self.requires]
        doc['outputs'] = OrderedDict()
        doc['outputs']['format'] = self.outputs.__doc__
        doc['outputs']['content_type'] = self.outputs.content_type
        parameters = [param for param in self.parameters if not param in ('request', 'response', 'self')
                      and not param in ('api_version', 'body')
                      and not param.startswith('hug_')
                      and not hasattr(param, 'directive')]
        if parameters:
            inputs = doc.setdefault('inputs', OrderedDict())
            types = self.interface.spec.__annotations__
            for argument in parameters:
                kind = types.get(argument, text)
                if getattr(kind, 'directive', None) is True:
                    continue

                input_definition = inputs.setdefault(argument, OrderedDict())
                input_definition['type'] = kind if isinstance(kind, str) else kind.__doc__
                default = self.defaults.get(argument, None)
                if default is not None:
                    input_definition['default'] = default

        return doc


class Local(Interface):
    """Defines the Interface responsible for exposing functions locally"""
    pass


class CLI(Interface):
    """Defines the Interface responsible for exposing functions to the CLI"""
    pass


class HTTP(Interface):
    """Defines the interface responsible for wrapping functions and exposing them via HTTP based on the route"""
    __slots__ = ('_params_for_outputs', '_params_for_invalid_outputs', '_params_for_transform', 'on_invalid',
                 '_params_for_on_invalid', 'set_status', 'response_headers', 'transform', 'input_transformations',
                 'examples', 'wrapped', 'catch_exceptions', 'parse_body', 'private')
    AUTO_INCLUDE = {'request', 'response'}

    def __init__(self, route, function, catch_exceptions=True):
        super().__init__(route, function)
        self.catch_exceptions = catch_exceptions
        self.parse_body = 'parse_body' in route
        self.set_status = route.get('status', False)
        self.response_headers = tuple(route.get('response_headers', {}).items())
        self.private = 'private' in route

        self._params_for_outputs = introspect.takes_arguments(self.outputs, *self.AUTO_INCLUDE)
        self._params_for_transform = introspect.takes_arguments(self.transform, *self.AUTO_INCLUDE)

        if 'output_invalid' in route:
            self._params_for_invalid_outputs = introspect.takes_arguments(self.invalid_outputs, *self.AUTO_INCLUDE)

        if 'on_invalid' in route:
            self._params_for_on_invalid = introspect.takes_arguments(self.on_invalid, *self.AUTO_INCLUDE)
        elif self.transform:
            self._params_for_on_invalid = self._params_for_transform

        if route['versions']:
            self.api.http.versions.update(route['versions'])

        self.interface.http = self

    async def gather_parameters(self, request, response, api_version=None, **input_parameters):
        """Gathers and returns all parameters that will be used for this endpoint"""
        paras = await request.post()
        input_parameters.update(paras)
        paras = request.GET
        input_parameters.update(paras)

        if self.parse_body and request.content_length:
            # body = request.stream
            body = request.content
            content_type, content_params = parse_content_type(request.content_type)
            body_formatter = self.api.http.input_format(content_type) if body else ''

            if body_formatter:
                body = await body_formatter(body, **content_params)
            if 'body' in self.all_parameters:
                input_parameters['body'] = body
            if isinstance(body, dict):
                input_parameters.update(body)
        elif 'body' in self.all_parameters:
            input_parameters['body'] = None

        if 'request' in self.all_parameters:
            input_parameters['request'] = request
        if 'response' in self.all_parameters:
            input_parameters['response'] = response
        if 'api_version' in self.all_parameters:
            input_parameters['api_version'] = api_version
        for parameter, directive in self.directives.items():
            arguments = (self.defaults[parameter],) if parameter in self.defaults else ()
            input_parameters[parameter] = directive(*arguments, response=response, request=request,
                                                    api=self.api, api_version=api_version, interface=self)

        return input_parameters

    @property
    def outputs(self):
        return getattr(self, '_outputs', self.api.http.output_format)

    @outputs.setter
    def outputs(self, outputs):
        self._outputs = outputs

    def transform_data(self, data, request=None, response=None):
        """Runs the transforms specified on this endpoint with the provided data, returning the data modified"""
        if self.transform and not (isinstance(self.transform, type) and isinstance(data, self.transform)):
            if self._params_for_transform:
                return self.transform(data, **self._arguments(self._params_for_transform, request, response))
            else:
                return self.transform(data)
        return data

    def content_type(self, request=None, response=None):
        """Returns the content type that should be used by default for this endpoint"""
        if callable(self.outputs.content_type):
            return self.outputs.content_type(request=request, response=response)
        else:
            return self.outputs.content_type

    def invalid_content_type(self, request=None, response=None):
        """Returns the content type that should be used by default on validation errors"""
        if callable(self.invalid_outputs.content_type):
            return self.invalid_outputs.content_type(request=request, response=response)
        else:
            return self.invalid_outputs.content_type

    def _arguments(self, requested_params, request=None, response=None):
        if requested_params:
            arguments = {}
            if 'response' in requested_params:
                arguments['response'] = response
            if 'request' in requested_params:
                arguments['request'] = request
            return arguments

        return empty.dict

    def set_response_defaults(self, response, request=None):
        """Sets up the response defaults that are defined in the URL route"""
        for header_name, header_value in self.response_headers:
            response.headers.update({header_name: header_value})
        if self.set_status:
            response.set_status(self.set_status)
        response.content_type = self.content_type(request, response)

    def render_errors(self, errors, request, response):
        response.set_status(400)
        data = {'errors': errors}
        if getattr(self, 'on_invalid', False):
            data = self.on_invalid(data, **self._arguments(self._params_for_on_invalid, request, response))

        if getattr(self, 'invalid_outputs', False):
            response.content_type = self.invalid_content_type(request, response)
            response.body = self.invalid_outputs(data, **self._arguments(self._params_for_invalid_outputs,
                                                                         request, response))
        else:
            response.body = self.outputs(data, **self._arguments(self._params_for_outputs, request, response))
        return response

    async def call_function(self, **parameters):
        if not self.interface.takes_kwargs:
            parameters = {key: value for key, value in parameters.items() if key in self.all_parameters}
        res = await self.interface(**parameters)
        return res

    async def render_content(self, content, request, response, **kwargs):
        if hasattr(content, 'interface') and (content.interface is True or hasattr(content.interface, 'http')):
            if content.interface is True:
                content(request, response, api_version=None, **kwargs)
            else:
                content.interface.http(request, response, api_version=None, **kwargs)
            return

        content = self.transform_data(content, request, response)
        content = self.outputs(content, **self._arguments(self._params_for_outputs, request, response))
        if hasattr(content, 'read'):
            size = None
            if hasattr(content, 'name') and os.path.isfile(content.name):
                size = os.path.getsize(content.name)
            if (request.headers.get('range', '') or request.headers.get('Range', '')) and size:
                start, end = request.headers['range'].split('=')[1].split('-')  # todo
                end = int(end)
                start = int(start)
                if end < 0:
                    end = size + end
                end = min(end, size)
                length = end - start + 1
                content.seek(start)
                response.body = content.read(length)
                response.set_status(206)
                response.content_range = (start, end, size)
                content.close()
            else:
                response.body = content.read()
                if size:
                    response.content_length = size
        else:
            response.body = content
        return response

    async def __call__(self, request, api_version=None, **kwargs):
        """Call the wrapped function over HTTP pulling information as needed"""
        response = sanic.web.Response()
        api_version = int(api_version) if api_version is not None else api_version
        if not self.catch_exceptions:
            exception_types = ()
        else:
            exception_types = self.api.http.exception_handlers(api_version)
            exception_types = tuple(exception_types.keys()) if exception_types else ()
        try:
            self.set_response_defaults(response, request)

            lacks_requirement = self.check_requirements(request, response)
            if lacks_requirement:
                response.body = self.outputs(lacks_requirement,
                                             **self._arguments(self._params_for_outputs, request, response))
                return response

            input_parameters = await self.gather_parameters(request, response, api_version, **kwargs)
            errors = self.validate(input_parameters)
            if errors:
                return self.render_errors(errors, request, response)

            res_content = await self.call_function(**input_parameters)
            return await self.render_content(res_content, request, response, **kwargs)
        except exception_types as exception:
            handler = None
            if type(exception) in exception_types:
                handler = self.api.http.exception_handlers(api_version)[type(exception)]
            else:
                for exception_type, exception_handler in \
                    tuple(self.api.http.exception_handlers(api_version).items())[::-1]:
                    if isinstance(exception, exception_type):
                        handler = exception_handler
            return await handler(request=request, exception=exception, **kwargs)

    def documentation(self, add_to=None, version=None, base_url="", url=""):
        """Returns the documentation specific to an HTTP interface"""
        doc = OrderedDict() if add_to is None else add_to

        usage = self.interface.spec.__doc__
        if usage:
            doc['usage'] = usage

        for example in self.examples:
            example_text = "{0}{1}{2}".format(base_url, '/v{0}'.format(version) if version else '', url)
            if isinstance(example, str):
                example_text += "?{0}".format(example)
            doc_examples = doc.setdefault('examples', [])
            if not example_text in doc_examples:
                doc_examples.append(example_text)

        doc = super().documentation(doc)

        if getattr(self, 'output_doc', ''):
            doc['outputs']['type'] = self.output_doc

        return doc

    @lru_cache()
    def urls(self, version=None):
        """Returns all URLS that are mapped to this interface"""
        urls = []
        for base_url, routes in self.api.http.routes.items():
            for url, methods in routes.items():
                for method, versions in methods.items():
                    for interface_version, interface in versions.items():
                        if interface_version == version and interface == self:
                            if not url in urls:
                                urls.append(('/v{0}'.format(version) if version else '') + url)
        return urls

    def url(self, version=None, **kwargs):
        """Returns the first matching URL found for the specified arguments"""
        for url in self.urls(version):
            if [key for key in kwargs.keys() if not '{' + key + '}' in url]:
                continue

            return url.format(**kwargs)

        raise KeyError('URL that takes all provided parameters not found')
