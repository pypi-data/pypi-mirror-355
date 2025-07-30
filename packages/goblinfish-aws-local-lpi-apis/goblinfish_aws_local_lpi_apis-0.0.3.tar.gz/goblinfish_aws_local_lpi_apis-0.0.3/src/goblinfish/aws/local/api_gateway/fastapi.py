#!/usr/bin/env python3.11
"""
"""

from __future__ import annotations

# Built-In Imports
import asyncio
import json
import logging
import os
import sys

from collections import namedtuple
from importlib import import_module
from inspect import iscoroutinefunction, isfunction, ismethod
from pathlib import Path
from pprint import pformat
from typing import Callable, NewType

# Third-Party Imports
from goblinfish.aws.local.api_gateway.helpers import \
    create_lambda_context, \
    get_external_function

try:
    from fastapi import FastAPI as _FastAPI, Request, Response
except ImportError as error:
    raise RuntimeError(
        f'{__file__.split(os.sep)[-1].split(os.extsep)[0]} could not '
        'import FastAPI from fastapi. Is the fastapi package installed?'
    ) from error

# Path Manipulations (avoid these!) and "Local" Imports

# Module "Constants" and Other Attributes
LambdaArguments = namedtuple('LambdaArguments', ['event', 'context'])
LambdaSpec = NewType('LambdaSpec', Callable | str)

logFormatter = logging.Formatter(f'[{__name__}] [%(levelname)s]  %(message)s')
logger = logging.getLogger(__name__)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())
# ~ logger.setLevel('INFO')

logger.debug(f'Created logger "{logger.name}"')


# Module Exceptions

# Module Functions
async def _extract_form_data(request) -> dict:
    try:
        logger.debug('Calling _extract_form_data:')
        logger.debug(pformat(vars()))
        logger.debug(f'headers: {request.headers}')
        form_data = await(request.form())
        logger.debug(f'returning {form_data}')
        return dict(form_data)
    except Exception as error:
        logger.exception(f'{error.__class__.__name__}: {error}')
        return {}


def _request_to_lambda_signature(request: Request) -> LambdaArguments:

    _headers = dict(request.headers)
    _content_type = _headers.get('content-type', '').lower()
    _query_strings = dict(request.query_params)

    # JSON data is the most common?
    if _content_type == 'application/json':
        _body = asyncio.run(request.body()).decode()
        _payload = json.dumps(json.loads(_body))

    # Standard form-data is the next most common?
    elif _content_type == 'application/x-www-form-urlencoded':
        _body = asyncio.run(request.body()).decode()
        _payload = json.dumps(
            {
                key_value.split('=')[0]: key_value.split('=')[1]
                for key_value in _body.split('&')
            }
        )

    # TODO: Figure out how to get file-uploads and multipart/form-data
    #       working. The test-harness may not be complete/correct?
    elif _content_type == 'multipart/form-data':
        raise NotImplementedError(
            'This package does not handle file uploads '
            '("multipart/form-data" POST submissions) yet.'
        )
        _form = asyncio.run(_extract_form_data(request))
        if _form:
            _payload = json.dumps(_form)
    else:
        _payload = ''

    event = {
        'resource': request.scope['path'],
        'path': request.scope['path'],
        'httpMethod': request.method,
        'headers': _headers,
        'multiValueHeaders': {
            key: value.split(', ')
            for key, value in _headers.items()
        },
        'queryStringParameters': _query_strings,
        'multiValueQueryStringParameters': {
            key: value.split(', ')
            for key, value in _query_strings.items()
        },
        'requestContext': {
            'httpMethod': request.method,
            'path': request.scope['path'],
            'protocol': request.scope['scheme'].upper()
            + '/' + request.scope['http_version'],
            'resourcePath': request.scope['path'],
        },
        'pathParameters': request.path_params,
        'body': _payload,
        'isBase64Encoded': False
    }
    context = create_lambda_context(event)

    result = LambdaArguments(event=event, context=context)
    logger.info(f'_request_to_lambda_signature completed')
    logger.debug(f'result: {result}')
    return result


def _lambda_result_to_response(response: dict):
    logger.info('Calling _request_to_lambda_signature:')
    logger.debug(pformat(vars()))
    logger.debug('request:')
    logger.debug(pformat(response))
    translated = {
        'content': response.get('body', ''),
        'status_code': response.get('statusCode', 200),
        'headers': response.get('headers', ''),
    }
    response_params = {
        key: value for key, value in translated.items() if value
    }
    response = Response(**response_params)
    logger.info(f'Returning {response}')
    return response

# Module Metaclasses

# Module Abstract Base Classes

# Module Concrete Classes
class FastAPI(_FastAPI):
    """
    Overrides the various HTTP-verb decorators provided by FastAPI, in
    order to allow an endpoint function to use a Lambda Function handler
    to provide the request processing and response generation for a
    local FastAPI application.
    """

    def delete(
        self,
        path: str,
        external_function: LambdaSpec | str,
        *args,
        **kwargs
    ) -> Callable:
        """
        Overrides the parent (FastAPI) decorator of the same name, to
        allow the specification of an external function that will be
        used to handle requests.

        Parameters:
        -----------
        path : str
            The path argument to be used in calling the parent class'
            method that this method overrides.
        external_function : LambdaSpec | str
            The "external" function to be wrapped and returned by the
            method
        *args : Any
            Any additional positional or listed arguments to be used
            in calling the parent class' method that this method
            overrides.
        **kwargs : Any
            Any keyword or keyword-only arguments to be used in
            calling the parent class' method that this method overrides.

        Notes:
        ------
        • The source code of the parent method is available online at
          github.com/fastapi/fastapi/blob/master/fastapi/applications.py
        • This function CAN be called rather than applied as a decorator.
          It will still return a viable result, which could be assigned
          to a name and used directly. For example:

          app = FastAPI()
          ...
          get_thing_endpoint = app.get(path, external_function)()
        """
        # At this layer, we're just getting the arguments passed.
        logger.debug(f'Calling {self.__class__.__name__}.get:')

        # Resolve the external function
        if isinstance(external_function, str):
            target_function = get_external_function(external_function)
        elif callable(external_function):
            target_function = external_function
        else:
            raise TypeError(
                f'Could not resolve "{external_function}" '
                f'({type(external_function).__name__})'
            )

        logger.debug(f'Resolved {target_function}')

        def _wrapper(target: Callable | None = None):
            """
            The initial function returned by the decoration process,
            which will be called by the Python runtime with the target
            function it is decorating, if used as a decorator.

            Parameters:
            -----------
            target : Callable | None
                The target function being decorated, if applicable.
            """
            # At this level, we're retrieving the target function
            # that is being decorated, if one was provided.
            logger.debug(
                f'Calling {self.__class__.__name__}.get.'
                '_wrapper:'
            )
            logger.debug(pformat(vars()))

            # Handle async vs. sync functions based on FastAPI's
            # apparent preferences and the target function, if one
            # has been provided
            if iscoroutinefunction(target):
                logger.info(f'Using async replacer for {getattr(target, "__name__", None)}.')
                async def _replacer(request: Request):
                    """
                    An async version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer (async):'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)
                    response = _lambda_result_to_response(results)
                    return response
            else:
                logger.info(f'Using sync replacer for {getattr(target, "__name__", None)}.')
                def _replacer(request: Request):
                    """
                    An async version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer:'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)

                    response = _lambda_result_to_response(results)
                    return response

            new_function = _FastAPI.delete(self, path, *args, **kwargs)(_replacer)
            logger.info(
                f'Returning {new_function.__name__} at '
                f'{hex(id(new_function))} to decorate {getattr(target, "__name__", None)}.'
            )
            return new_function

        return _wrapper

    def get(
        self,
        path: str,
        external_function: LambdaSpec | str,
        *args,
        **kwargs
    ) -> Callable:
        """
        Overrides the parent (FastAPI) decorator of the same name, to
        allow the specification of an external function that will be
        used to handle requests.

        Parameters:
        -----------
        path : str
            The path argument to be used in calling the parent class'
            method that this method overrides.
        external_function : LambdaSpec | str
            The "external" function to be wrapped and returned by the
            method
        *args : Any
            Any additional positional or listed arguments to be used
            in calling the parent class' method that this method
            overrides.
        **kwargs : Any
            Any keyword or keyword-only arguments to be used in
            calling the parent class' method that this method overrides.

        Notes:
        ------
        • The source code of the parent method is available online at
          github.com/fastapi/fastapi/blob/master/fastapi/applications.py
        • This function CAN be called rather than applied as a decorator.
          It will still return a viable result, which could be assigned
          to a name and used directly. For example:

          app = FastAPI()
          ...
          get_thing_endpoint = app.get(path, external_function)()
        """
        # At this layer, we're just getting the arguments passed.
        logger.debug(f'Calling {self.__class__.__name__}.get:')

        # Resolve the external function
        if isinstance(external_function, str):
            target_function = get_external_function(external_function)
        elif callable(external_function):
            target_function = external_function
        else:
            raise TypeError(
                f'Could not resolve "{external_function}" '
                f'({type(external_function).__name__})'
            )

        logger.debug(f'Resolved {target_function}')

        def _wrapper(target: Callable | None = None):
            """
            The initial function returned by the decoration process,
            which will be called by the Python runtime with the target
            function it is decorating, if used as a decorator.

            Parameters:
            -----------
            target : Callable | None
                The target function being decorated, if applicable.
            """
            # At this level, we're retrieving the target function
            # that is being decorated, if one was provided.
            logger.debug(
                f'Calling {self.__class__.__name__}.get.'
                '_wrapper:'
            )
            logger.debug(pformat(vars()))

            # Handle async vs. sync functions based on FastAPI's
            # apparent preferences and the target function, if one
            # has been provided
            if iscoroutinefunction(target):
                logger.info(f'Using async replacer for {getattr(target, "__name__", None)}.')
                async def _replacer(request: Request):
                    """
                    An async version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer (async):'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)
                    response = _lambda_result_to_response(results)
                    return response
            else:
                logger.info(f'Using sync replacer for {getattr(target, "__name__", None)}.')
                def _replacer(request: Request):
                    """
                    A sync version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer:'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)

                    response = _lambda_result_to_response(results)
                    return response

            new_function = _FastAPI.get(self, path, *args, **kwargs)(_replacer)
            logger.info(
                f'Returning {new_function.__name__} at '
                f'{hex(id(new_function))} to decorate {getattr(target, "__name__", None)}.'
            )
            return new_function

        return _wrapper

    def head(
        self,
        path: str,
        external_function: LambdaSpec | str,
        *args,
        **kwargs
    ) -> Callable:
        """
        Overrides the parent (FastAPI) decorator of the same name, to
        allow the specification of an external function that will be
        used to handle requests.

        Parameters:
        -----------
        path : str
            The path argument to be used in calling the parent class'
            method that this method overrides.
        external_function : LambdaSpec | str
            The "external" function to be wrapped and returned by the
            method
        *args : Any
            Any additional positional or listed arguments to be used
            in calling the parent class' method that this method
            overrides.
        **kwargs : Any
            Any keyword or keyword-only arguments to be used in
            calling the parent class' method that this method overrides.

        Notes:
        ------

        Notes:
        ------
        • The source code of the parent method is available online at
          github.com/fastapi/fastapi/blob/master/fastapi/applications.py
        • This function CAN be called rather than applied as a decorator.
          It will still return a viable result, which could be assigned
          to a name and used directly. For example:

          app = FastAPI()
          ...
          head_thing_endpoint = app.head(path, external_function)()
        """
        # At this layer, we're just getting the arguments passed.
        logger.debug(f'Calling {self.__class__.__name__}.head:')
        logger.debug(pformat(vars()))
        # Resolve the external function
        if isinstance(external_function, str):
            target_function = get_external_function(external_function)
            logger.debug(f'### target_function: {target_function}')
        elif callable(external_function):
            target_function = external_function
        else:
            raise TypeError(
                f'Could not resolve "{external_function}" '
                f'({type(external_function).__name__})'
            )

        logger.debug(f'Resolved {target_function}')

        def _wrapper(target: Callable | None = None):
            """
            The initial function returned by the decoration process,
            which will be called by the Python runtime with the target
            function it is decorating, if used as a decorator.

            Parameters:
            -----------
            target : Callable | None
                The target function being decorated, if applicable.
            """
            # At this level, we're retrieving the target function
            # that is being decorated, if one was provided.
            logger.debug(
                f'Calling {self.__class__.__name__}.head.'
                '_wrapper:'
            )
            logger.debug(pformat(vars()))

            # Handle async vs. sync functions based on FastAPI's
            # apparent preferences and the target function, if one
            # has been provided
            if iscoroutinefunction(target):
                logger.info(f'Using async replacer for {getattr(target, "__name__", None)}.')
                async def _replacer(request: Request):
                    """
                    An async version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer (async):'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)
                    response = _lambda_result_to_response(results)
                    return response
            else:
                logger.info(f'Using sync replacer for {getattr(target, "__name__", None)}.')
                def _replacer(request: Request):
                    """
                    A sync version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer:'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)

                    response = _lambda_result_to_response(results)
                    return response

            new_function = _FastAPI.head(self, path, *args, **kwargs)(_replacer)
            logger.info(
                f'Returning {new_function.__name__} at '
                f'{hex(id(new_function))} to decorate {getattr(target, "__name__", None)}.'
            )
            return new_function

        return _wrapper


    def options(
        self,
        path: str,
        external_function: LambdaSpec | str,
        *args,
        **kwargs
    ) -> Callable:
        """
        Overrides the parent (FastAPI) decorator of the same name, to
        allow the specification of an external function that will be
        used to handle requests.

        Parameters:
        -----------
        path : str
            The path argument to be used in calling the parent class'
            method that this method overrides.
        external_function : LambdaSpec | str
            The "external" function to be wrapped and returned by the
            method
        *args : Any
            Any additional positional or listed arguments to be used
            in calling the parent class' method that this method
            overrides.
        **kwargs : Any
            Any keyword or keyword-only arguments to be used in
            calling the parent class' method that this method overrides.

        Notes:
        ------
        • The source code of the parent method is available online at
          github.com/fastapi/fastapi/blob/master/fastapi/applications.py
        • This function CAN be called rather than applied as a decorator.
          It will still return a viable result, which could be assigned
          to a name and used directly. For example:

          app = FastAPI()
          ...
          options_thing_endpoint = app.options(path, external_function)()
        """
        # At this layer, we're just getting the arguments passed.
        logger.debug(f'Calling {self.__class__.__name__}.options:')
        logger.debug(pformat(vars()))
        # Resolve the external function
        if isinstance(external_function, str):
            target_function = get_external_function(external_function)
            logger.debug(f'### target_function: {target_function}')
        elif callable(external_function):
            target_function = external_function
        else:
            raise TypeError(
                f'Could not resolve "{external_function}" '
                f'({type(external_function).__name__})'
            )

        logger.debug(f'Resolved {target_function}')

        def _wrapper(target: Callable | None = None):
            """
            The initial function returned by the decoration process,
            which will be called by the Python runtime with the target
            function it is decorating, if used as a decorator.

            Parameters:
            -----------
            target : Callable | None
                The target function being decorated, if applicable.
            """
            # At this level, we're retrieving the target function
            # that is being decorated, if one was provided.
            logger.debug(
                f'Calling {self.__class__.__name__}.options.'
                '_wrapper:'
            )
            logger.debug(pformat(vars()))

            # Handle async vs. sync functions based on FastAPI's
            # apparent preferences and the target function, if one
            # has been provided
            if iscoroutinefunction(target):
                logger.info(f'Using async replacer for {getattr(target, "__name__", None)}.')
                async def _replacer(request: Request):
                    """
                    An async version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer (async):'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)
                    response = _lambda_result_to_response(results)
                    return response
            else:
                logger.info(f'Using sync replacer for {getattr(target, "__name__", None)}.')
                def _replacer(request: Request):
                    """
                    A sync version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer:'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)

                    response = _lambda_result_to_response(results)
                    return response

            new_function = _FastAPI.options(self, path, *args, **kwargs)(_replacer)
            logger.info(
                f'Returning {new_function.__name__} at '
                f'{hex(id(new_function))} to decorate {getattr(target, "__name__", None)}.'
            )
            return new_function

        return _wrapper


    def patch(
        self,
        path: str,
        external_function: LambdaSpec | str,
        *args,
        **kwargs
    ) -> Callable:
        """
        Overrides the parent (FastAPI) decorator of the same name, to
        allow the specification of an external function that will be
        used to handle requests.

        Parameters:
        -----------
        path : str
            The path argument to be used in calling the parent class'
            method that this method overrides.
        external_function : LambdaSpec | str
            The "external" function to be wrapped and returned by the
            method
        *args : Any
            Any additional positional or listed arguments to be used
            in calling the parent class' method that this method
            overrides.
        **kwargs : Any
            Any keyword or keyword-only arguments to be used in
            calling the parent class' method that this method overrides.

        Notes:
        ------
        • The source code of the parent method is available online at
          github.com/fastapi/fastapi/blob/master/fastapi/applications.py
        • This function CAN be called rather than applied as a decorator.
          It will still return a viable result, which could be assigned
          to a name and used directly. For example:

          app = FastAPI()
          ...
          patch_thing_endpoint = app.patch(path, external_function)()
        """
        # At this layer, we're just getting the arguments passed.
        logger.debug(f'Calling {self.__class__.__name__}.patch:')
        logger.debug(pformat(vars()))
        # Resolve the external function
        if isinstance(external_function, str):
            target_function = get_external_function(external_function)
            logger.debug(f'### target_function: {target_function}')
        elif callable(external_function):
            target_function = external_function
        else:
            raise TypeError(
                f'Could not resolve "{external_function}" '
                f'({type(external_function).__name__})'
            )

        logger.debug(f'Resolved {target_function}')

        def _wrapper(target: Callable | None = None):
            """
            The initial function returned by the decoration process,
            which will be called by the Python runtime with the target
            function it is decorating, if used as a decorator.

            Parameters:
            -----------
            target : Callable | None
                The target function being decorated, if applicable.
            """
            # At this level, we're retrieving the target function
            # that is being decorated, if one was provided.
            logger.debug(
                f'Calling {self.__class__.__name__}.patch.'
                '_wrapper:'
            )
            logger.debug(pformat(vars()))

            # Handle async vs. sync functions based on FastAPI's
            # apparent preferences and the target function, if one
            # has been provided
            if iscoroutinefunction(target):
                logger.info(f'Using async replacer for {getattr(target, "__name__", None)}.')
                async def _replacer(request: Request):
                    """
                    An async version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer (async):'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)
                    response = _lambda_result_to_response(results)
                    return response
            else:
                logger.info(f'Using sync replacer for {getattr(target, "__name__", None)}.')
                def _replacer(request: Request):
                    """
                    A sync version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer:'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)

                    response = _lambda_result_to_response(results)
                    return response

            new_function = _FastAPI.patch(self, path, *args, **kwargs)(_replacer)
            logger.info(
                f'Returning {new_function.__name__} at '
                f'{hex(id(new_function))} to decorate {getattr(target, "__name__", None)}.'
            )
            return new_function

        return _wrapper

    def post(
        self,
        path: str,
        external_function: LambdaSpec | str,
        *args,
        **kwargs
    ) -> Callable:
        """
        Overrides the parent (FastAPI) decorator of the same name, to
        allow the specification of an external function that will be
        used to handle requests.

        Parameters:
        -----------
        path : str
            The path argument to be used in calling the parent class'
            method that this method overrides.
        external_function : LambdaSpec | str
            The "external" function to be wrapped and returned by the
            method
        *args : Any
            Any additional positional or listed arguments to be used
            in calling the parent class' method that this method
            overrides.
        **kwargs : Any
            Any keyword or keyword-only arguments to be used in
            calling the parent class' method that this method overrides.

        Notes:
        ------
        • The source code of the parent method is available online at
          github.com/fastapi/fastapi/blob/master/fastapi/applications.py
        • This function CAN be called rather than applied as a decorator.
          It will still return a viable result, which could be assigned
          to a name and used directly. For example:

          app = FastAPI()
          ...
          post_thing_endpoint = app.post(path, external_function)()
        """
        # At this layer, we're just getting the arguments passed.
        logger.debug(f'Calling {self.__class__.__name__}.post:')
        logger.debug(pformat(vars()))
        # Resolve the external function
        if isinstance(external_function, str):
            target_function = get_external_function(external_function)
            logger.debug(f'### target_function: {target_function}')
        elif callable(external_function):
            target_function = external_function
        else:
            raise TypeError(
                f'Could not resolve "{external_function}" '
                f'({type(external_function).__name__})'
            )

        logger.debug(f'Resolved {target_function}')

        def _wrapper(target: Callable | None = None):
            """
            The initial function returned by the decoration process,
            which will be called by the Python runtime with the target
            function it is decorating, if used as a decorator.

            Parameters:
            -----------
            target : Callable | None
                The target function being decorated, if applicable.
            """
            # At this level, we're retrieving the target function
            # that is being decorated, if one was provided.
            logger.debug(
                f'Calling {self.__class__.__name__}.post.'
                '_wrapper:'
            )
            logger.debug(pformat(vars()))

            # Handle async vs. sync functions based on FastAPI's
            # apparent preferences and the target function, if one
            # has been provided
            if iscoroutinefunction(target):
                logger.info(f'Using async replacer for {getattr(target, "__name__", None)}.')
                async def _replacer(request: Request):
                    """
                    An async version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer (async):'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)
                    response = _lambda_result_to_response(results)
                    return response
            else:
                logger.info(f'Using sync replacer for {getattr(target, "__name__", None)}.')
                def _replacer(request: Request):
                    """
                    A sync version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer:'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)

                    response = _lambda_result_to_response(results)
                    return response

            new_function = _FastAPI.post(self, path, *args, **kwargs)(_replacer)
            logger.info(
                f'Returning {new_function.__name__} at '
                f'{hex(id(new_function))} to decorate {getattr(target, "__name__", None)}.'
            )
            return new_function

        return _wrapper

    def put(
        self,
        path: str,
        external_function: LambdaSpec | str,
        *args,
        **kwargs
    ) -> Callable:
        """
        Overrides the parent (FastAPI) decorator of the same name, to
        allow the specification of an external function that will be
        used to handle requests.

        Parameters:
        -----------
        path : str
            The path argument to be used in calling the parent class'
            method that this method overrides.
        external_function : LambdaSpec | str
            The "external" function to be wrapped and returned by the
            method
        *args : Any
            Any additional positional or listed arguments to be used
            in calling the parent class' method that this method
            overrides.
        **kwargs : Any
            Any keyword or keyword-only arguments to be used in
            calling the parent class' method that this method overrides.

        Notes:
        ------
        • The source code of the parent method is available online at
          github.com/fastapi/fastapi/blob/master/fastapi/applications.py
        • This function CAN be called rather than applied as a decorator.
          It will still return a viable result, which could be assigned
          to a name and used directly. For example:

          app = FastAPI()
          ...
          put_thing_endpoint = app.put(path, external_function)()
        """
        # At this layer, we're just getting the arguments passed.
        logger.debug(f'Calling {self.__class__.__name__}.put:')
        logger.debug(pformat(vars()))
        # Resolve the external function
        if isinstance(external_function, str):
            target_function = get_external_function(external_function)
            logger.debug(f'### target_function: {target_function}')
        elif callable(external_function):
            target_function = external_function
        else:
            raise TypeError(
                f'Could not resolve "{external_function}" '
                f'({type(external_function).__name__})'
            )

        logger.debug(f'Resolved {target_function}')

        def _wrapper(target: Callable | None = None):
            """
            The initial function returned by the decoration process,
            which will be called by the Python runtime with the target
            function it is decorating, if used as a decorator.

            Parameters:
            -----------
            target : Callable | None
                The target function being decorated, if applicable.
            """
            # At this level, we're retrieving the target function
            # that is being decorated, if one was provided.
            logger.debug(
                f'Calling {self.__class__.__name__}.put.'
                '_wrapper:'
            )
            logger.debug(pformat(vars()))

            # Handle async vs. sync functions based on FastAPI's
            # apparent preferences and the target function, if one
            # has been provided
            if iscoroutinefunction(target):
                logger.info(f'Using async replacer for {getattr(target, "__name__", None)}.')
                async def _replacer(request: Request):
                    """
                    An async version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer (async):'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)
                    response = _lambda_result_to_response(results)
                    return response
            else:
                logger.info(f'Using sync replacer for {getattr(target, "__name__", None)}.')
                def _replacer(request: Request):
                    """
                    A sync version of the function that will be returned,
                    replacing a decorator target where applicable.
                    """
                    logger.debug(
                        f'Calling {self.__class__.__name__}.get.'
                        '_wrapper._replacer:'
                    )

                    event, context = _request_to_lambda_signature(request)
                    results = target_function(event, context)

                    response = _lambda_result_to_response(results)
                    return response

            new_function = _FastAPI.put(self, path, *args, **kwargs)(_replacer)
            logger.info(
                f'Returning {new_function.__name__} at '
                f'{hex(id(new_function))} to decorate {getattr(target, "__name__", None)}.'
            )
            return new_function

        return _wrapper

# Code to run if the module is executed directly
if __name__ == '__main__':
    pass
