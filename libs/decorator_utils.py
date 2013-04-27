from threading import Timer


def delay_keys(time, key_func=None):
    """ Delay given function so that calls
    in short intervals result in one call.

    Only calls with arguments that are the same for key_func(*args, **kwargs)
    are masked and delayed.
    """
    delayed_calls = dict()

    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            key = key_func(*args, **kwargs)

            def callback():
                del delayed_calls[key]

                # bind `func` to `self`
                bound_func = func.__get__(self, self.__class__)
                bound_func(*args, **kwargs)

            if key in delayed_calls and delayed_calls[key].is_alive():
                delayed_calls[key].cancel()

            delayed_calls[key] = Timer(time, callback)
            delayed_calls[key].start()

        return decorated_func

    return decorator


def delay(time):
    """ Delay given function """
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            def callback():
                # bind `func` to `self`
                bound_func = func.__get__(self, self.__class__)
                bound_func(*args, **kwargs)

            delay_timer = Timer(time, callback)
            delay_timer.start()

        return decorated_func

    return decorator
