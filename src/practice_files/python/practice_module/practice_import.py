import importlib.util
import sys


def main():
    spec = importlib.util.find_spec(
        "practice_dataclass_conversion", "practice_builtins"
    )

    if spec is None:
        print("Cannot find pytz package.")
    else:
        to_dict = importlib.util.module_from_spec(spec)

        to_dict = spec.loader.load_module()

        spec.loader.exec_module(to_dict)


if __name__ == "__main__":
    main()
