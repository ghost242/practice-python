"""
Practice for decorator with arguments.

* CASE 1. call function, no arguments and not called `deco` 
* CASE 2. call function, call `deco` with arguments
* CASE 3. call function with keyword arguments, call `deco` with empty arguments
* CASE 4. call function with kwargs, call `deco` with empty arguments
* CASE 5. call function with every argument types, call `deco` with kwargs to put attribute on inner function.
"""

from functools import wraps


def deco(*args, **kwargs):    
    print("on deco", args, kwargs)
    def _deco(fn):
        print("on _deco", args, kwargs)
        @wraps(fn)
        def inner_fn(*args_, **kwargs_):
            print(f"on inner_fn({fn.__qualname__}) | {args=}, {kwargs=}")
            print(f"on inner_fn({fn.__qualname__}) | {args_=}, {kwargs_=}")
            print(f"on inner_fn({fn.__qualname__}) | ", f"call function({fn.__qualname__}) with deco")

            return fn(*args_, **kwargs_)
    
        # If put attribute on decorated function(inner_fn, not fn)
        for k,v  in kwargs.items():
            setattr(inner_fn, k, v)

        return inner_fn
    
    if len(args) > 0 and callable(args[0]):
        fn, *args = args
        return _deco(fn)
    else:
        return _deco


@deco
def func1(a: int):
    print("in func >>", "Hello" * a)
    return 1


@deco(1,2,3,4,5)
def func2(u,v,w,x,y):
    print("in func >>", u,v,w,x,y)
    return 2

@deco()
def func3(*, dt):
    print("in func >>", dt)

    return 3

@deco()
def func4(**kwargs):
    print("in func >>", kwargs)
    return 4

@deco(t=10, r=20, s=30)
def func5(a, /, x, y, z, *args, **kwargs):
    print(a, x, y, z)

    print(func5.t, func5.r, func5.s)
    print(getattr(func5, "t"), getattr(func5, "r"), getattr(func5, "s"))
    
    return 5

if __name__ == "__main__":    
    """
    Print out stdbuf

    on deco (<function func1 at 0x100831160>,) {}
    on _deco [] {}
    on deco (1, 2, 3, 4, 5) {}
    on _deco (1, 2, 3, 4, 5) {}
    on deco () {}
    on _deco () {}
    on deco () {}
    on _deco () {}
    on deco () {'t': 10, 'r': 20, 's': 30}
    on _deco () {'t': 10, 'r': 20, 's': 30}
    on inner_fn(func1) | args=[], kwargs={}
    on inner_fn(func1) | args_=(10,), kwargs_={}
    on inner_fn(func1) |  call function(func1) with deco
    in func >> HelloHelloHelloHelloHelloHelloHelloHelloHelloHello
    func1>>
    1
    >>func1
    on inner_fn(func2) | args=(1, 2, 3, 4, 5), kwargs={}
    on inner_fn(func2) | args_=('u', 'v', 'w', 'x', 'y'), kwargs_={}
    on inner_fn(func2) |  call function(func2) with deco
    in func >> u v w x y
    func2>>
    2
    >>func2
    on inner_fn(func3) | args=(), kwargs={}
    on inner_fn(func3) | args_=(), kwargs_={'dt': 100}
    on inner_fn(func3) |  call function(func3) with deco
    in func >> 100
    func3>>
    3
    >>func3
    on inner_fn(func4) | args=(), kwargs={}
    on inner_fn(func4) | args_=(), kwargs_={'i': 10, 'j': 'a', 'k': (5+10j)}
    on inner_fn(func4) |  call function(func4) with deco
    in func >> {'i': 10, 'j': 'a', 'k': (5+10j)}
    func4>>
    4
    >>func4
    on inner_fn(func5) | args=(), kwargs={'t': 10, 'r': 20, 's': 30}
    on inner_fn(func5) | args_=(1, 2, 3, 4), kwargs_={}
    on inner_fn(func5) |  call function(func5) with deco
    1 2 3 4
    10 20 30
    10 20 30
    func5>>
    5
    >>func5
    """

    print("func1>>", func1(10), ">>func1", sep='\n')
    print("func2>>", func2('u','v','w','x','y'), ">>func2", sep='\n')
    print("func3>>", func3(dt=100), ">>func3", sep='\n')
    print("func4>>", func4(i=10,j='a',k=5+10j), ">>func4", sep='\n')
    print("func5>>", func5(1,2,3,4), ">>func5", sep='\n')
