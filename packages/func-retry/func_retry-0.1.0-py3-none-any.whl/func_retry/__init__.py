import asyncio
import functools
import time
from typing import Optional, Callable, Awaitable, Union, Tuple, Dict

Callback = Optional[Callable[[Exception, int, Tuple, Dict], Union[Awaitable, None]]]


def retry(exc=Exception, times: Optional[int] = 3, delay: Optional[int] = None,
          callback: Callback = None):
    """
    Retry

    Args:
        exc : **Exception** Exception or Subclass of Exception
        times : **Optional[int]** Max retry times. Default to **3**.
            When set to `None`, it will continue to retry until successful
        delay: **Optional[int]** Delay seconds. Default to **None**.
        callback: **Optional[Callable[[Exception, int, Tuple, Dict], Union[Awaitable, None]]]**

    Returns:

    """

    def do_try(current_times, total_times):
        if total_times is None:
            return True
        return current_times <= total_times

    def decorator_retry(func):
        @functools.wraps(func)
        async def async_retry(*args, **kwargs):
            current_retry_times = 0
            while do_try(current_retry_times, times):
                try:
                    return await func(*args, **kwargs)
                except exc as e:
                    if callback:
                        await callback(e, current_retry_times, args, kwargs)
                    current_retry_times += 1
                    if delay:
                        await asyncio.sleep(delay)

        @functools.wraps(func)
        def sync_retry(*args, **kwargs):
            current_retry_times = 0
            while do_try(current_retry_times, times):
                try:
                    return func(*args, **kwargs)
                except exc as e:
                    if callback:
                        callback(e, current_retry_times, args, kwargs)
                    current_retry_times += 1
                    if delay:
                        time.sleep(delay)

        # 判断函数是否为异步函数
        if asyncio.iscoroutinefunction(func):
            return async_retry
        else:
            return sync_retry

    return decorator_retry
