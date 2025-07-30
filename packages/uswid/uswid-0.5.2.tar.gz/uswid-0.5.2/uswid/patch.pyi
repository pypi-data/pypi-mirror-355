from enum import Enum

class uSwidPatchType(str, Enum):
    UNKNOWN = 'unknown'
    BACKPORT = 'backport'
    CHERRY_PICK = 'cherry-pick'
    SECURITY = 'security'
    @staticmethod
    def from_str(value: str) -> uSwidPatchType: ...

class uSwidPatch:
    type: uSwidPatchType
    url: str | None
    description: str | None
    references: list[str]
    def __init__(self, type: uSwidPatchType = ..., url: str | None = None, description: str | None = None, references: list[str] | None = None) -> None: ...
