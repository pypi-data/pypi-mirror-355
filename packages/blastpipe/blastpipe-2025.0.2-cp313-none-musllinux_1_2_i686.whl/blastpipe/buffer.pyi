import asyncio

from . import public

@public
async def prefixed_send(stream: asyncio.StreamWriter, buffer: bytes) -> None:
    ...

@public
async def prefixed_recv(stream: asyncio.StreamReader) -> bytes:
    ...
