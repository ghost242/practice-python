def main():
    fn_header = "def func(a:str,b:str):\n"
    fn_body = "    print(a, b)\n"

    values = dict()
    namespace = dict()
    exec(fn_header + fn_body, values, namespace)

    # print(values)
    print(namespace)

    namespace["func"](10, 20)


if __name__ == "__main__":
    main()
