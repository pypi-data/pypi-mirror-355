#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from functools import wraps
from typing import Any

from typer import Exit

from pendingai.cli.console import Console
from pendingai.exceptions import PendingAiError

cerr = Console(stderr=True)


def catch_exception(exception: type[Exception] = PendingAiError, code: int = 1):
    """
    App command decorator for capturing an exception class, rendering a
    formatted error message and exiting the app with status code.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            try:
                return func(*args, **kwargs)
            except exception as e:
                cerr.print(f"[red bold]{e.__class__.__name__}:[/] {str(e)}")
                raise Exit(code=code)

        return wrapper

    return decorator
