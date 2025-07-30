from .component import uSwidComponent as uSwidComponent
from .problem import uSwidProblem as uSwidProblem
from enum import IntEnum

class uSwidLinkRel(IntEnum):
    LICENSE = -2
    COMPILER = -1
    UNKNOWN = 0
    ANCESTOR = 1
    COMPONENT = 2
    FEATURE = 3
    INSTALLATION_MEDIA = 4
    PACKAGE_INSTALLER = 5
    PARENT = 6
    PATCHES = 7
    REQUIRES = 8
    SEE_ALSO = 9
    SUPERSEDES = 10
    SUPPLEMENTAL = 11
    @classmethod
    def from_string(cls, value: str) -> uSwidLinkRel: ...

class uSwidLinkUse(IntEnum):
    OPTIONAL = 1
    REQUIRED = 2
    RECOMMENDED = 3

class uSwidLink:
    use: uSwidLinkUse | None
    component: uSwidComponent | None
    def __init__(self, href: str | None = None, rel: uSwidLinkRel | None = None, use: uSwidLinkUse | None = None, spdx_id: str | None = None) -> None: ...
    @property
    def spdx_id(self) -> str | None: ...
    @property
    def rel(self) -> uSwidLinkRel | None: ...
    @rel.setter
    def rel(self, rel: uSwidLinkRel | None) -> None: ...
    @property
    def href(self) -> str | None: ...
    @href.setter
    def href(self, href: str | None) -> None: ...
    @property
    def href_for_display(self) -> str | None: ...
    def problems(self) -> list[uSwidProblem]: ...
