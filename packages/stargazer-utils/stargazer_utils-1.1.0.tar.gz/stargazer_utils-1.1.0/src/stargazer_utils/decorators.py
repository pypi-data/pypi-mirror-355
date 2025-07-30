"""
A collection of decorators. Well, just the one right now.

### Legal
SPDX-FileCopyright © 2025 Robert Ferguson <rmferguson@pm.me>

SPDX-License-Identifier: [MIT](https://spdx.org/licenses/MIT.html)
"""

import functools
import random
import time
from typing import Any, Callable, Type, TypeVar, Union, cast

__all__ = [
    "exponential_retry",
]

F = TypeVar("F", bound=Callable[..., Any])


def exponential_retry(
    caught_exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] | None = None,
    max_tries: int = 3,
    base_delay: float = 2,
) -> Callable[[F], F]:
    """
    An exponential retry function, intended to consume API ~~or scrape pages~~ where you don't necessarily know the rate limit ahead of time,
    but can be adapted for less surriptitious code as well.

    Uses a slight jitter on the delay for... reasons.
    """

    if caught_exceptions is None:
        caught_exceptions = (Exception,)

    def deco_retry(f: F) -> F:
        @functools.wraps(f)
        def f_retry(*args: Any, **kwargs: Any) -> Any:
            tries_left = max_tries - 1
            delay = base_delay + random.uniform(0, 1)
            while tries_left > 0:
                try:
                    return f(*args, **kwargs)
                except caught_exceptions:
                    time.sleep(delay)

                    tries_left -= 1
                    expo = max_tries - tries_left
                    delay = (base_delay**expo) + random.uniform(0, 1)

            # Try last time without a catch.
            return f(*args, **kwargs)

        return cast(F, f_retry)

    return deco_retry
