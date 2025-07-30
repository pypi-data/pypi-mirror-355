from .problem import uSwidProblem as uSwidProblem
from enum import IntEnum

class uSwidEntityRole(IntEnum):
    TAG_CREATOR = 1
    SOFTWARE_CREATOR = 2
    AGGREGATOR = 3
    DISTRIBUTOR = 4
    LICENSOR = 5
    MAINTAINER = 6

class uSwidEntity:
    name: str | None
    regid: str | None
    roles: list[uSwidEntityRole]
    def __init__(self, name: str | None = None, regid: str | None = None, roles: list[uSwidEntityRole] | None = None) -> None: ...
    def add_role(self, role: uSwidEntityRole) -> None: ...
    def problems(self) -> list[uSwidProblem]: ...
