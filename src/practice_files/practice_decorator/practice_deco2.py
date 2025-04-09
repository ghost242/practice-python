from functools import wraps


class c:
    def __call__(self, f):
        val = 100

        @wraps(f)
        def wrapper(*args, **kwargs):
            print("called wrapper deco: {}".format(val))
            return f(*args, **kwargs)

        return wrapper


deco = c()


@deco
def func(t):
    """
    param t: somethings value
    type: object
    return: t
    return_type: object
    """
    print("called function: {}".format(t))
    return t


func(10)

print(func.__closure__)
print(func.__code__.co_varnames)
print(func.__code__.co_argcount)
