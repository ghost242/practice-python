def html_tag(tag):
    def deco(func):
        def wrapper():
            nonlocal tag
            return "<{0}>{1}</{0}>".format(tag, func())

        return wrapper

    return deco


@html_tag("p")
@html_tag("a")
def text():
    return "hello"


print(text())
