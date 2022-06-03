import time
import logging
import logging.config
from random import randrange
from functools import wraps


def backoff(
    _caller: str,
    _logger: logging.Logger = None,
    start_sleep_time=0.1, factor=2, border_sleep_time=10
):
    """
    Функция для повторного выполнения функции через некоторое время,
    если возникла ошибка. Использует наивный экспоненциальный рост времени
    повтора (factor) до граничного времени ожидания (border_sleep_time)
    Формула:
        t = start_sleep_time * 2^(n) if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time

    :param _caller: вызвавшая функция
    :param _logger: объект логгера
    :param start_sleep_time: начальное время повтора
    :param factor: во сколько раз нужно увеличить время ожидания
    :param border_sleep_time: граничное время ожидания
    :return: результат выполнения функции
    """

    if _logger:
        log = _logger
    else:
        log = logging.getLogger()

    def waiting(attempt: int):
        delay = start_sleep_time * pow(factor, attempt)
        if delay > border_sleep_time:
            delay = border_sleep_time
        log.debug(
            'Attempt %d in <%s>. Retry after %s sec',
            attempt, _caller, delay
        )
        time.sleep(delay)

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            """Выполнить декорируемую функцию с ее параметрами"""
            attempt = 1
            while True:
                try:
                    return func(*args, **kwargs)
                except BaseException as err:
                    log.error('%s', err)
                    waiting(attempt)
                    # if attempt == 10:
                    #     break
                    attempt += 1

        return inner

    return func_wrapper


logging.config.fileConfig('logging.conf')


@backoff('backoff.test')
def test():  # Decorator test function
    r = randrange(1, 10)
    if r < 2:
        return 'Done'
    else:
        raise BaseException('Error value', r)
        time.sleep(3)


if __name__ == '__main__':
    logging.debug('%s', test())
