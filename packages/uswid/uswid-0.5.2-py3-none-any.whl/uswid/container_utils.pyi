from .component import uSwidComponent as uSwidComponent
from .container import uSwidContainer as uSwidContainer
from .entity import uSwidEntity as uSwidEntity, uSwidEntityRole as uSwidEntityRole
from .enums import uSwidVersionScheme as uSwidVersionScheme
from .format_coswid import uSwidFormatCoswid as uSwidFormatCoswid
from .format_cyclonedx import uSwidFormatCycloneDX as uSwidFormatCycloneDX
from .format_goswid import uSwidFormatGoswid as uSwidFormatGoswid
from .format_ini import uSwidFormatIni as uSwidFormatIni
from .format_pkgconfig import uSwidFormatPkgconfig as uSwidFormatPkgconfig
from .format_spdx import uSwidFormatSpdx as uSwidFormatSpdx
from .format_swid import uSwidFormatSwid as uSwidFormatSwid
from .format_uswid import uSwidFormatUswid as uSwidFormatUswid

def container_generate(container: uSwidContainer) -> None: ...
def container_roundtrip(container: uSwidContainer, verbose: bool = False) -> None: ...
