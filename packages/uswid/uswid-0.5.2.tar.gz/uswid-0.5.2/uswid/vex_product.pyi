from .hash import uSwidHash as uSwidHash, uSwidHashAlg as uSwidHashAlg
from .purl import uSwidPurl as uSwidPurl

class uSwidVexProduct:
    tag_ids: list[uSwidPurl]
    hashes: list[uSwidHash]
    def __init__(self) -> None: ...
