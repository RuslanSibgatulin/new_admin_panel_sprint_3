from functools import wraps
import time


def backoff(start_sleep_time=0.1, factor=2, border_sleep_time=10):
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
        print('Attempt', attempt, 'Waiting for', delay, 'sec')
        time.sleep(delay)

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            """Выполнить декорируемую функцию с ее параметрами"""
            attempt = 1
            while True:
                try:
                    print('Try to exec function:', func.__name__)
                    func(*args, **kwargs)
                    break
                except ConnectionError:
                    waiting(attempt)
                    if attempt == 10:
                        break
                    attempt += 1

        return inner

    return func_wrapper


@backoff(0.3)
def connect():
    print('Connecting...')
    raise ConnectionError


if __name__ == '__main__':
    connect()
