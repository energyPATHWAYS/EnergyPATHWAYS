import config
import shape
import util
import dispatch_classes
import pathways_model

from .generated.new_database import _Metadata, EnergyPathwaysDatabase

#
# These methods form the API between a subclass of CsvDatabase and the validation subsystem.
#
def get_metadata():
    return _Metadata

def database_class():
    return EnergyPathwaysDatabase
