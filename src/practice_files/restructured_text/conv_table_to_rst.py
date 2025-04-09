import re


def conv_to_rst(raw_tb_set, width=120):
    """
    markdown like table

    :return:
    """

    regexr = re.compile(r"---(|---)*")

    tb_lines = list(map(lambda i: i.strip(), raw_tb_set.split("\n")))
    if regexr.match(tb_lines[1]):  # if header exists, it is header separator
        header, _, *body = tb_lines
        header = list(header.split("|"))
        body = [b.split("|") for b in body]
    else:
        header = None
        body = [b.split("|") for b in tb_lines]

    pass
