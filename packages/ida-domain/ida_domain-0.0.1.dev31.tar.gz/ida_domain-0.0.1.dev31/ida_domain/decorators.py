from __future__ import annotations
import functools
import inspect
import ida_ua


class DatabaseNotLoadedError(RuntimeError):
    """Raised when an operation is attempted on a closed database."""

    pass


def decorate_all_methods(decorator):
    """
    Class decorator factory that applies `decorator` to all methods
    of the class (excluding dunder methods).
    """

    def decorate(cls):
        for name, attr in cls.__dict__.items():
            if name.startswith('__'):
                continue
            if callable(attr):
                setattr(cls, name, decorator(attr))
        return cls

    return decorate


def check_db_open(fn):
    """
    Decorator that checks that a database is open.
    """

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        # Check inside database class
        if hasattr(self, 'is_open'):
            if not self.is_open():
                raise DatabaseNotLoadedError(
                    f'{fn.__qualname__}: Database is not loaded. Please open a database first.'
                )

        # Check entities that reference a database instance
        if hasattr(self, 'm_database'):
            if not self.m_database.is_open():
                raise DatabaseNotLoadedError(
                    f'{fn.__qualname__}: Database is not loaded. Please open a database first.'
                )

        return fn(self, *args, **kwargs)

    return wrapper


def check_insn_valid():
    """
    Decorator that checks if any ida_ua.insn_t parameters are valid using self.is_valid().
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            # Get function signature to map args to parameter names
            sig = inspect.signature(fn)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()

            # Check each parameter
            for param_name, param_value in bound_args.arguments.items():
                if param_name == 'self':
                    continue

                # Check if parameter is an insn_t instance
                if isinstance(param_value, ida_ua.insn_t):
                    if hasattr(self, 'is_valid') and not self.is_valid(param_value):
                        raise ValueError(
                            f'{fn.__qualname__}: Invalid instruction parameter "{param_name}"'
                        )

            return fn(self, *args, **kwargs)

        return wrapper

    return decorator
