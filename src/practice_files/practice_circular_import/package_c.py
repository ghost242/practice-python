name_c = "C"


def func_c():
    from practice_circular_import import name_a

    print(f"c in {name_a}")
