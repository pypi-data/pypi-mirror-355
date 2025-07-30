from .component import uSwidComponent as uSwidComponent, uSwidComponentType as uSwidComponentType
from .container import uSwidContainer as uSwidContainer
from .entity import uSwidEntity as uSwidEntity, uSwidEntityRole as uSwidEntityRole
from .errors import NotSupportedError as NotSupportedError
from .format import uSwidFormatBase as uSwidFormatBase
from .link import uSwidLink as uSwidLink, uSwidLinkRel as uSwidLinkRel
from .purl import uSwidPurl as uSwidPurl
from .vcs import uSwidVcs as uSwidVcs

class uSwidFormatInf(uSwidFormatBase):
    def __init__(self) -> None: ...
    def incorporate(self, container: uSwidContainer, component: uSwidComponent) -> None: ...
    def load(self, blob: bytes, path: str | None = None) -> uSwidContainer: ...
