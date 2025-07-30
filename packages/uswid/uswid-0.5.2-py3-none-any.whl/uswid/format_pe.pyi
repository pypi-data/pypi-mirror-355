from .container import uSwidContainer as uSwidContainer
from .errors import NotSupportedError as NotSupportedError
from .format import uSwidFormatBase as uSwidFormatBase
from .format_coswid import uSwidFormatCoswid as uSwidFormatCoswid

class uSwidFormatPe(uSwidFormatBase):
    objcopy: str | None
    cc: str | None
    cflags: str | None
    filepath: str | None
    def __init__(self, filepath: str | None = None) -> None: ...
    def load(self, blob: bytes, path: str | None = None) -> uSwidContainer: ...
    def save(self, container: uSwidContainer) -> bytes: ...
