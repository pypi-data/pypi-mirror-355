from .component import uSwidComponent as uSwidComponent
from .container import uSwidContainer as uSwidContainer
from .enums import USWID_HEADER_MAGIC as USWID_HEADER_MAGIC, uSwidHeaderFlags as uSwidHeaderFlags, uSwidPayloadCompression as uSwidPayloadCompression
from .errors import NotSupportedError as NotSupportedError
from .format import uSwidFormatBase as uSwidFormatBase
from .format_coswid import uSwidFormatCoswid as uSwidFormatCoswid

class uSwidFormatUswid(uSwidFormatBase):
    compression: uSwidPayloadCompression
    def __init__(self, compress: bool = False, compression: uSwidPayloadCompression = ...) -> None: ...
    @property
    def compress(self) -> bool: ...
    def load(self, blob: bytes, path: str | None = None) -> uSwidContainer: ...
    def save(self, container: uSwidContainer) -> bytes: ...
