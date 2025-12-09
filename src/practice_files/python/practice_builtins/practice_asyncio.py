from concurrent import futures
import asyncio
import random
import contextlib


async def func(n):
    print(n)
    await asyncio.sleep(5)


@contextlib.asynccontextmanager
async def file_handle(fname):
    yield open(fname)


async def aiter():
    for n in range(100):
        yield n


async def amain():
    await func(10)

    async for num in aiter():
        print(num)

    async with file_handle(
        "",
    ) as fd:
        content = fd.read()
        print(content)


def main():
    with futures.ThreadPoolExecutor(max_workers=5) as executor:
        future = executor.submit(func, random.randint(1, 100))


if __name__ == "__main__":
    # asyncio.run(amain())

    amain()

    # main()
