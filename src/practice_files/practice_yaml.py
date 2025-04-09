from io import StringIO

import yaml


def main():
    raw = """
Key1: &KEY_REF asdf
Key2: 
    - *KEY_REF 
    - zxcv
    - - 1234
      - 5678
      - qwer
    """

    raw_stream = StringIO(raw)
    res = yaml.safe_load(raw_stream)

    print(res)


if __name__ == "__main__":
    main()
