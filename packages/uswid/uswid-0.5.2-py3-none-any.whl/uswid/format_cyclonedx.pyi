from .component import uSwidComponent as uSwidComponent, uSwidComponentType as uSwidComponentType
from .container import uSwidContainer as uSwidContainer
from .entity import uSwidEntity as uSwidEntity, uSwidEntityRole as uSwidEntityRole
from .enums import uSwidVersionScheme as uSwidVersionScheme
from .errors import NotSupportedError as NotSupportedError
from .evidence import uSwidEvidence as uSwidEvidence
from .format import uSwidFormatBase as uSwidFormatBase
from .hash import uSwidHash as uSwidHash, uSwidHashAlg as uSwidHashAlg
from .link import uSwidLink as uSwidLink, uSwidLinkRel as uSwidLinkRel
from .patch import uSwidPatch as uSwidPatch, uSwidPatchType as uSwidPatchType
from .payload import uSwidPayload as uSwidPayload

class uSwidFormatCycloneDX(uSwidFormatBase):
    serial_number: str | None
    timestamp: str | None
    def __init__(self) -> None: ...
    def load(self, blob: bytes, path: str | None = None) -> uSwidContainer: ...
    def save(self, container: uSwidContainer) -> bytes: ...
