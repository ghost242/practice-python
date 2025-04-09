from flask import Flask

app123 = Flask(__name__)


@app123.route("/")
def index():
    return "<h1>Hello world!!</h1>"


def mapper(f, *s):
    m = dict()

    def wrapper():
        r = f()
        m[s[0]] = r

    return wrapper


@mapper("hello")
def func():
    return 1000


if __name__ == "__main__":
    app123.run()

# include <random>
# define TRUE rand() % 2
# define FALSE rand() % 2
