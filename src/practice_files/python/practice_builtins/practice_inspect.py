import inspect


def func(a, b, c):
    frame = inspect.currentframe()
    super_frame = frame.f_back

    sig = inspect.signature(func)
    this = super_frame.f_globals["func"]
    setattr(this, "new_attr", "new_attribute")

    print("sig.parameters.keys()", sig.parameters.keys())
    print("frame.f_globals", frame.f_globals)
    print("frame.f_locals", frame.f_locals)
    print("frame.f_back", super_frame)
    print("frame.f_back.f_locals", super_frame.f_locals)
    print("this.attr", this.attr)
    print(
        "params: ",
        ", ".join(
            [
                f"{k}: {v}"
                for k, v in frame.f_locals.items()
                if k in sig.parameters.keys()
            ]
        ),
    )
    print("params", a, b, c)


def main():
    setattr(func, "attr", "new_function")

    func(10, "x", 1 + 5j)

    print(func.new_attr)


if __name__ == "__main__":
    main()
