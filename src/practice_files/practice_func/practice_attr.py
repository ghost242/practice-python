def func():
    print(getattr(func, "attr_1"))

setattr(func, "attr_1", 1234)

func()

def sub_func():
    from practice_files.practice_func.practice_attr_2 import func

    print("in sub_func", func.attr_1)

sub_func()

print(func.attr_1)