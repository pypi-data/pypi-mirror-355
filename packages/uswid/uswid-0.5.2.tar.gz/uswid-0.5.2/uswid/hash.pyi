from enum import IntEnum

class uSwidHashAlg(IntEnum):
    UNKNOWN = 0
    SHA256 = 1
    SHA384 = 7
    SHA512 = 8
    SHA1 = -1
    @classmethod
    def from_string(cls, alg_id: str) -> uSwidHashAlg: ...

class uSwidHash:
    alg_id: uSwidHashAlg | None
    def __init__(self, alg_id: uSwidHashAlg | None = None, value: str | None = None) -> None: ...
    @property
    def alg_id_for_display(self) -> str | None: ...
    @property
    def value(self) -> str | None: ...
    @value.setter
    def value(self, value: str | None) -> None: ...
