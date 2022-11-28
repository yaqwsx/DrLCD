from contextlib import contextmanager
from typing import Generator, List
from serial import Serial # type: ignore

class Machine:
    def __init__(self, port: Serial) -> None:
        self._port = port

    @contextmanager
    def _preserveTimeout(self) -> Generator[None, None, None]:
        originalTimeout = self._port.timeout
        try:
            yield
        finally:
            self._port.timeout = originalTimeout

    def waitForBoot(self) -> None:
        """
        Wait for the board to boot up - that is there are no new info is echoed
        """
        with self.preserveTimeout():
            self._port.timeout = 2
            while True:
                line = self._port.readline().decode("utf-8")
                if line == "":
                    return

    def command(self, command: str, timeout: float=10) -> List[str]:
        """
        Issue G-code command, waits for completion and returns a list of
        returned values (lines of response)
        """
        if not command.endswith("\n"):
            command += "\n"
        with self._preserveTimeout():
            # Clear pending data
            self._port.timeout = None
            self._port.read_all()
            # Send command
            self._port.write(command.encode("utf-8"))
            # Wait for response
            response = []
            self._port.timeout = timeout
            while True:
                line = self._port.readline().decode("utf-8")
                if line == "":
                    raise TimeoutError(f"No response on command {command.strip()}")
                line = line.strip()
                if line.endswith("ok"):
                    if line[:-2] != "":
                        response.append(line[:-2])
                    return response
                response.append(line)


@contextmanager
def machineConnection(port: str) -> Generator[Machine, None, None]:
    with Serial(port) as s:
        yield Machine(s)
