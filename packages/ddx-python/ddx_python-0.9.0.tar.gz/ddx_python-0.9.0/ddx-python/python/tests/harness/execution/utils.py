import functools
from typing import Union, get_args, get_origin, get_type_hints

from ddx.common.logging import CHECKMARK, local_logger


def format_type_hint(type_hint):
    # Handling the most common generic types such as Union, Optional, List, etc.
    origin = get_origin(type_hint)
    if origin:
        args = get_args(type_hint)
        # Special case for Optional as a common alias for Union[type, None]
        if (
            origin == Union
            and len(args) == 2
            and any(arg is type(None) for arg in args)
        ):
            non_none_arg = next(arg for arg in args if arg is not type(None))
            return f"Optional[{format_type_hint(non_none_arg)}]"
        # Join arguments for other generics like Union, List, etc.
        args_formatted = ", ".join(format_type_hint(arg) for arg in args)
        return f"{origin.__name__}[{args_formatted}]"

    # Simple case where type_hint is a type
    if hasattr(type_hint, "__name__"):
        return type_hint.__name__

    # Fallback for other cases
    return str(type_hint)


def log_success(req_type):
    def _log_success(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            req_name = req_type.__name__
            logger = local_logger(__name__)
            logger.success(
                f"{CHECKMARK} - processing request {req_name}; arrived at new state root hash ({str(self.root)})"
            )
            result = func(self, *args, **kwargs)
            logger.success(
                f"{CHECKMARK * 2} - processed {format_type_hint(ret_type) if (ret_type := get_type_hints(func).get('return')) else 'UnknownTxs'} from {req_name}; arrived at new state root hash ({str(self.root)})"
            )
            return result

        return wrapper

    return _log_success
