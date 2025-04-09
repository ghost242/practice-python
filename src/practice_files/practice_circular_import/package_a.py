name_a = "A"


def func_a():
    from practice_circular_import import name_b

    print(f"a in {name_b}")
