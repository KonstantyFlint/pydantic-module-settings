import asyncio


class Config:
    PORT: int = 1


async def coroutine():
    PORT: int = 2
    return PORT


def function():
    PORT: int = 3
    return PORT


CLASS_PORT = Config.PORT
ASYNC_PORT = asyncio.run(coroutine())
LOCAL_PORT = function()
