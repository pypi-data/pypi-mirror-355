from .component import uSwidComponent as uSwidComponent
from .container import uSwidContainer as uSwidContainer
from .entity import uSwidEntity as uSwidEntity
from .errors import NotSupportedError as NotSupportedError
from .evidence import uSwidEvidence as uSwidEvidence
from .format import uSwidFormatBase as uSwidFormatBase
from .hash import uSwidHash as uSwidHash, uSwidHashAlg as uSwidHashAlg
from .link import uSwidLink as uSwidLink, uSwidLinkRel as uSwidLinkRel
from .payload import uSwidPayload as uSwidPayload

class uSwidFormatGoswid(uSwidFormatBase):
    def __init__(self) -> None: ...
    def load(self, blob: bytes, path: str | None = None) -> uSwidContainer: ...
    def save(self, container: uSwidContainer) -> bytes: ...
