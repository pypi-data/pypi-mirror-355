
from .Parsers import ElectronicStructureLogReader

__all__ = [
    "OrcaLogReader"
]

class OrcaLogReader(ElectronicStructureLogReader):
    components_name = "OrcaLogComponents"