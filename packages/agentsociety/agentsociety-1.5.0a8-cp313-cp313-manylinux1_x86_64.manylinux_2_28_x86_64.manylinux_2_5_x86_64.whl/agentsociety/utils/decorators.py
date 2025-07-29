import functools
import inspect
import time
import traceback

from ..logger import get_logger

CALLING_STRING = 'function: `{func_name}` in "{file_path}", line {line_number}, arguments: `{arguments}` start time: `{start_time}` end time: `{end_time}` output: `{output}`'

LOCK_CALLING_START_STRING = 'Start Lock - function: `{func_name}` in "{file_path}", line {line_number}, arguments: `{arguments}` start time: `{start_time}`'

LOCK_CALLING_END_STRING = 'Release Lock - function: `{func_name}` in "{file_path}", line {line_number}, arguments: `{arguments}` end time: `{end_time}` output: `{output}`'

LOCK_CALLING_EXCEPTION_STRING = 'Release Lock With Exception - function: `{func_name}` in "{file_path}", line {line_number}, arguments: `{arguments}` start time: `{start_time}` Exception: `{exception}`'

__all__ = [
    "record_call_aio",
    "record_call",
    "lock_decorator",
    "log_execution_time",
]


def record_call_aio(record_function_calling: bool = True):
    """
    Decorator to log the async function call details if `record_function_calling` is True.
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            cur_frame = inspect.currentframe()
            assert cur_frame is not None
            frame = cur_frame.f_back
            assert frame is not None
            line_number = frame.f_lineno
            file_path = frame.f_code.co_filename
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            if record_function_calling:
                print(
                    CALLING_STRING.format(
                        func_name=func,
                        line_number=line_number,
                        file_path=file_path,
                        arguments=signature,
                        start_time=start_time,
                        end_time=end_time,
                        output=result,
                    )
                )
            return result

        return wrapper

    return decorator


def record_call(record_function_calling: bool = True):
    """
    Decorator to log the function call details if `record_function_calling` is True.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            cur_frame = inspect.currentframe()
            assert cur_frame is not None
            frame = cur_frame.f_back
            assert frame is not None
            line_number = frame.f_lineno
            file_path = frame.f_code.co_filename
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            if record_function_calling:
                print(
                    CALLING_STRING.format(
                        func_name=func,
                        line_number=line_number,
                        file_path=file_path,
                        arguments=signature,
                        start_time=start_time,
                        end_time=end_time,
                        output=result,
                    )
                )
            return result

        return wrapper

    return decorator


def lock_decorator(func):
    async def wrapper(self, *args, **kwargs):
        lock = self._lock
        await lock.acquire()
        line_number = None
        file_path = None
        signature = None
        start_time = None
        try:
            cur_frame = inspect.currentframe()
            assert cur_frame is not None
            frame = cur_frame.f_back
            assert frame is not None
            line_number = frame.f_lineno
            file_path = frame.f_code.co_filename
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            start_time = time.time()
            get_logger().debug(
                LOCK_CALLING_START_STRING.format(
                    func_name=func,
                    line_number=line_number,
                    file_path=file_path,
                    arguments=signature,
                    start_time=start_time,
                )
            )
            result = await func(self, *args, **kwargs)
            end_time = time.time()
            get_logger().debug(
                LOCK_CALLING_END_STRING.format(
                    func_name=func,
                    line_number=line_number,
                    file_path=file_path,
                    arguments=signature,
                    end_time=end_time,
                    output=result,
                )
            )
            return result
        except Exception as e:
            # traceback
            exception_str = traceback.format_exc()
            get_logger().debug(
                LOCK_CALLING_EXCEPTION_STRING.format(
                    func_name=func,
                    line_number=line_number,
                    file_path=file_path,
                    arguments=signature,
                    start_time=start_time,
                    exception=exception_str,
                )
            )
            raise e
        finally:
            lock.release()

    return wrapper


def log_execution_time(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        start_time = time.time()
        log = {"req": func.__name__, "start_time": start_time, "consumption": 0}
        result = await func(self, *args, **kwargs)
        log["consumption"] = time.time() - start_time
        # add log to log list
        self._log_list.append(log)
        return result

    return wrapper
