import functools
import logging
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def disney_property(
    refresh: bool = True, default_value: Optional[T] = None
) -> Callable[[Callable[[Any], Optional[T]]], property]:
    """Simplify getting data from objects that implement lazy loading.

    Args:
        refresh (bool, optional): Call the object's refresh method before attempting to get data. Defaults to True.
        default_value (Optional[T], optional): Default value to return if there is an error. Defaults to None.

    Returns:
        Callable[[Callable[[Any], Optional[T]]], property]: The decorator
    """

    def decorator(func: Callable) -> property:
        @functools.wraps(func)
        def wrapper(self: Any) -> Optional[T]:
            if refresh:
                self.refresh()
            try:
                return func(self)
            except (KeyError, TypeError, ValueError):
                logger.debug("No data found for disney property %s, returning default value", func.__name__)
                return default_value

        wrapper.__annotations__ = func.__annotations__
        wrapper.__doc__ = func.__doc__
        return property(wrapper)

    return decorator


def json_property(func: Callable) -> property:
    """Simplify getting data from the Disney responses.

    Args:
        func (Callable): The function to wrap

    Returns:
        property: The value from the json response as a property.
    """

    @property
    @functools.wraps(func)
    def wrapper(self: Any) -> Any:
        try:
            return func(self)
        except (KeyError, TypeError, ValueError):
            logger.debug("No data found for json property %s", func.__name__)
            return None

    return wrapper
