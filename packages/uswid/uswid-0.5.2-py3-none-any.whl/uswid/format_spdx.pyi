from .component import uSwidComponent as uSwidComponent
from .container import uSwidContainer as uSwidContainer
from .entity import uSwidEntity as uSwidEntity, uSwidEntityRole as uSwidEntityRole
from .errors import NotSupportedError as NotSupportedError
from .format import uSwidFormatBase as uSwidFormatBase
from .hash import uSwidHashAlg as uSwidHashAlg
from .link import uSwidLink as uSwidLink, uSwidLinkRel as uSwidLinkRel

class uSwidFormatSpdx(uSwidFormatBase):
    def __init__(self) -> None: ...
    def load(self, blob: bytes, path: str | None = None) -> uSwidContainer: ...
    def save(self, container: uSwidContainer) -> bytes: ...
