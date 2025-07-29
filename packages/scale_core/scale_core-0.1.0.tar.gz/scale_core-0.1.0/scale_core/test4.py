import asyncio
from time import perf_counter

from scale import AsyncThreadPoolExecutor, Scale

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )

# _base.LOGGER.setLevel(logging.DEBUG)

scale = Scale()


@scale.scale(print)
async def test(iterations=1000000):
    s = 0
    for i in range(iterations):
        s += i * i
    return s


async def test2(iterations=1000000):  # то же самое но без scale
    s = 0
    for i in range(iterations):
        s += i * i
    return s


async def main():
    start = perf_counter()
    for i in range(200):
        result = await test(i * 1000)
    await asyncio.sleep(0.01)
    end = perf_counter()
    print(f'Time: {end - start}')


async def main2():
    async with AsyncThreadPoolExecutor() as executor:
        start = perf_counter()
        for i in range(200):
            result = await executor.submit(test2, i * 1000)
            print(await result)
        end = perf_counter()
        print(f'Time: {end - start}')


async def main3():
    start = perf_counter()
    for i in range(200):
        result = await test2(i * 1000)
        print(i)
    end = perf_counter()
    print(f'Time: {end - start}')


asyncio.run(main())
# asyncio.run(main2())
# asyncio.run(main3())

scale.stop()
