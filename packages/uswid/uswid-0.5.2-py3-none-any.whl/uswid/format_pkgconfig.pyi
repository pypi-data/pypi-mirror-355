from .component import uSwidComponent as uSwidComponent, uSwidComponentType as uSwidComponentType
from .container import uSwidContainer as uSwidContainer
from .entity import uSwidEntityRole as uSwidEntityRole
from .format import uSwidFormatBase as uSwidFormatBase

class uSwidFormatPkgconfig(uSwidFormatBase):
    filepath: str | None
    def __init__(self, filepath: str | None = None) -> None: ...
    def load(self, blob: bytes, path: str | None = None) -> uSwidContainer: ...
