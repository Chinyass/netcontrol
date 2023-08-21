class NoController(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UnsupportedFunctionalityException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SnmpTooBigException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class TelnetNoAuthDataException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)