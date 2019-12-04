
# modules should be imported here
import config
import shape
import util
import dispatch_classes
import pathways_model

#
# These methods form the API between a subclass of CsvDatabase and the validation subsystem.
#
def get_metadata():
    from .generated.new_database import _Metadata
    return _Metadata

def database_class():
    from .generated.new_database import EnergyPathwaysDatabase
    return EnergyPathwaysDatabase
