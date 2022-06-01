import time
import logging
from random import randrange
from functools import wraps


def retry(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as err:
                logger.debug('retry called by error: %s', err)
                time.sleep(5)
    return wrapper


def backoff(
    caller: str,
    start_sleep_time=0.1, factor=2, border_sleep_time=10
):
    """
    Функция для повторного выполнения функции через некоторое время,
    если возникла ошибка. Использует наивный экспоненциальный рост времени
    повтора (factor) до граничного времени ожидания (border_sleep_time)
    Формула:
        t = start_sleep_time * 2^(n) if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time

    :param start_sleep_time: начальное время повтора
    :param factor: во сколько раз нужно увеличить время ожидания
    :param border_sleep_time: граничное время ожидания
    :return: результат выполнения функции
    """

    def waiting(attempt: int):
        delay = start_sleep_time * pow(factor, attempt)
        if delay > border_sleep_time:
            delay = border_sleep_time
        logging.debug(
            'Attempt %d in <%s>. Retry after %s sec',
            attempt, caller, delay
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
                    logging.error('%s', err)
                    waiting(attempt)
                    # if attempt == 10:
                    #     break
                    attempt += 1

        return inner

    return func_wrapper


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('back')


@backoff('backoff.test', logger, 0.3)
def test():  # Decorator test function
    r = randrange(1, 10)
    if r < 2:
        return 'Done'
    else:
        raise BaseException('Error value', r)
        time.sleep(3)


if __name__ == '__main__':
    logger.debug('%s', test())
