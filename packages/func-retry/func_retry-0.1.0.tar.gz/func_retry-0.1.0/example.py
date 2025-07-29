# @Time     : 2025/6/13 10:00
# @Software : Python 3.10
# @About    :
from func_retry import retry


def callback_func(current_error, current_retry_times, input_args, input_kwargs):
    print(f"Retry {current_retry_times} times, error: {current_error},Input -> {input_args} {input_kwargs}")


async def acallback_func(current_error, current_retry_times, input_args, input_kwargs):
    print(f"Retry {current_retry_times} times, error: {current_error},Input -> {input_args} {input_kwargs}")


@retry(times=3, delay=1, callback=callback_func)
def test_func1(key):
    print(f"start run test_func1 --> {key}")
    raise Exception("test_func1 error")


@retry(times=3, delay=1, callback=acallback_func)
async def test_func2(key):
    print(f"start run test_func2 --> {key}")
    raise Exception("test_func2 error")


@retry(times=None, delay=1, callback=callback_func)
def test_func3(key):
    print(f"start run test_func3 --> {key}")
    raise Exception("test_func3 error")


if __name__ == '__main__':
    test_func1('A')

    import asyncio

    asyncio.run(test_func2('B'))

    # test_func3('C')
