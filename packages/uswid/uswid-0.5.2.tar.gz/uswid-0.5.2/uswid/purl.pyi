class uSwidPurl:
    scheme: str | None
    protocol: str | None
    namespace: str | None
    name: str | None
    version: str | None
    qualifiers: str | None
    subpath: str | None
    def __init__(self, value: str | None = None) -> None: ...
    def parse(self, value: str) -> None: ...
    def matches(self, other: uSwidPurl) -> bool: ...
