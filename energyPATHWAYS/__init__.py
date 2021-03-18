from energyPATHWAYS import config
from energyPATHWAYS import shape
from energyPATHWAYS import util
from energyPATHWAYS import dispatch_classes
from energyPATHWAYS import pathways_model

from .generated.new_database import _Metadata, EnergyPathwaysDatabase

#
# These methods form the API between a subclass of CsvDatabase and the validation subsystem.
#
def get_metadata():
    return _Metadata

def database_class():
    return EnergyPathwaysDatabase
