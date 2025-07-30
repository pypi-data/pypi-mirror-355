from collections.abc import Callable
from typing import Any

from botocore.exceptions import ClientError


class ClientErrorHandler:
    def __init__(
        self,
        error_code: str,
        exception_class: type[Exception],
    ) -> None:
        self.__error_code = error_code
        self.__exception_class = exception_class

    def __call__(self, f: Callable[..., Any]) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return f(*args, **kwargs)
            except ClientError as e:
                error = e.response["Error"]
                if error.get("QueryErrorCode", error["Code"]) == self.__error_code:
                    raise self.__exception_class from e

                raise

        return wrapper
