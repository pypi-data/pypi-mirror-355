import asyncio
import logging
from typing import Any, cast

_LOGGER = logging.getLogger(__name__)


class ProcessReturnCodeError(Exception):
    code: int
    stdout: bytes | None
    stderr: bytes | None

    def __init__(self, *args: Any, code: int, stdout: bytes | None, stderr: bytes | None):
        super().__init__(f"Process ended with code {code}", *args, stderr)
        self.code = code
        self.stdout = stdout
        self.stderr = stderr


async def _write(process: asyncio.subprocess.Process, data: bytes | None):
    if data is not None:
        stdin = cast(asyncio.StreamWriter, process.stdin)
        try:
            stdin.write(data)
            await stdin.drain()
        except ConnectionResetError:
            pass
        stdin.close()


async def run(*command: str, input: bytes | None = None) -> None:
    _LOGGER.info("running subprocess: %s", command)
    process = await asyncio.subprocess.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE if input is not None else None,
    )

    code, _none = await asyncio.gather(process.wait(), _write(process, input))

    if code != 0:
        raise ProcessReturnCodeError(code=code, stdout=None, stderr=None)


async def run_output(*command: str, input: bytes | None = None) -> tuple[bytes, bytes]:
    _LOGGER.info("running subprocess: %s", command)
    process = await asyncio.subprocess.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE if input is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr, code, _none = await asyncio.gather(
        cast(asyncio.StreamReader, process.stdout).read(),
        cast(asyncio.StreamReader, process.stderr).read(),
        process.wait(),
        _write(process, input),
    )

    if code != 0:
        raise ProcessReturnCodeError(code=code, stdout=stdout, stderr=stderr)

    return stdout, stderr
