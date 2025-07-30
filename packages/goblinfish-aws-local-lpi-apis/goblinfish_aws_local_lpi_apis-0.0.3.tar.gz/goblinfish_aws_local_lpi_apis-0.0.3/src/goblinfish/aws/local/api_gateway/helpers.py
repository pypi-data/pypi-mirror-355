#!/usr/bin/env python3.11
"""
"""

from __future__ import annotations

# Built-In Imports
import logging
import os
import sys

from datetime import datetime, timedelta
from functools import cache
from importlib import import_module
from uuid import uuid4

# Third-Party Imports
from awslambdaric.lambda_context import LambdaContext

# Path Manipulations (avoid these!) and "Local" Imports

# Module "Constants" and Other Attributes
logFormatter = logging.Formatter(f'[{__name__}] [%(levelname)s]  %(message)s')
logger = logging.getLogger('app')

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())

logger.debug(f'Created logger "{logger.name}"')

# Module Exceptions

# Module Functions
def create_lambda_context(
    event: dict,
    timeout_seconds: int = 900
) -> LambdaContext:
    """
    """
    now = datetime.now()
    deadline_offset = timedelta(seconds=timeout_seconds)
    context = LambdaContext(
        invoke_id=str(uuid4()),
        client_context = event,
        cognito_identity = None,
        epoch_deadline_time_in_ms = int(
            (now + deadline_offset).timestamp()*1000
        ),
        invoked_function_arn = None,
        # ~ tenant_id = None,
    )
    logger.info(
        f'Created {context} with {context.get_remaining_time_in_millis()} '
        'ms remaining before timeout.'
    )
    return context


@cache
def get_external_function(namespace: str) -> Callable:
    # Import it using the provided namespace path and
    # make sure it's a function or method
    module_name = '.'.join(namespace.split('.')[:-1])
    function_name = namespace.split('.')[-1]
    logger.debug(f'## Importing {function_name} from {module_name}')
    try:
        external_function = getattr(
            import_module(module_name), function_name
        )
        logger.debug(f'## Imported {external_function}')
        return external_function
    except (ModuleNotFoundError, ImportError) as error:
        logger.debug(f'### sys.path: {sys.path}')
        logger.exception(
            f'The import of {namespace} ({function_name} from ' \
            f'{module_name}) raised ' \
            f'{error.__class__.__name__}: {error}'
        )
        raise

# Module Metaclasses

# Module Abstract Base Classes

# Module Concrete Classes

# Code to run if the module is executed directly
if __name__ == '__main__':
    pass

    print(get_external_function('people.crud_operations.read_people'))
