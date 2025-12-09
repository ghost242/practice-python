name_b = "B"


def func_b():
    from practice_circular_import import name_c

    print(f"b in {name_c}")
