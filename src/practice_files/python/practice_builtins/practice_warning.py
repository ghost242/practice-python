import logging
import warnings


def raise_exception():
    raise RuntimeError("exception message")


def main():
    print("common work line")

    # warnings.warn("warning message", RuntimeWarning)

    warnings.warn(
        "Google Ads V5 will deprecate June 23, 2021",
        DeprecationWarning,
    )

    print("common work message")

    # try:
    #     raise_exception()
    # except RuntimeError as e:
    #     logging.exception("exception message", exc_info=e)


if __name__ == "__main__":
    main()
