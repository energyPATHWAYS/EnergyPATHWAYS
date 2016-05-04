import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from sqlalchemy import MetaData
import pandas as pd
from numbers import Number


class Base(object):
    def _quoted_attr_value(self, key):
        """
        Looks up self's attribute with the name contained in the key parameter.
        If the attribute's value is a number or is None, return it unadorned,
        otherwise return it wrapped in double quotes.
        """
        val = getattr(self, key)
        return val if isinstance(val, Number) or val is None else '"%s"' % (val,)

    def __repr__(self):
        attr_strs = ["%s=%s" % (key, self._quoted_attr_value(key)) for key in self.__mapper__.columns.keys()]

        # This version gets all attributes, not just the columns you'd set in the constructor. That feels too verbose
        # to me for general use, but could be helpful for debugging.
        # attr_strs = ['%s=%s' % (attr.key, attr.value) for attr in sa.inspect(self).attrs]

        return type(self).__name__ + '(' + ', '.join(attr_strs) + ')'


# TODO: (MAC) this explicit metadata is only needed during this transitional migration period;
# once we're done migrating, everything SQLAlchemy needs will be in the default public schema again
Base = declarative_base(cls=Base, metadata=MetaData(schema='migrated'))


# For now we are expecting config to reach in and kick this since it has the config information
def init(db_conf):
    global engine
    engine = sa.create_engine(URL(**db_conf)) #,echo=True
    global MakeSession
    MakeSession = sa.orm.sessionmaker(bind=engine)
    global load_session
    load_session = MakeSession()


def fetch(cls, **kwargs):
    result = load_session.query(cls).filter_by(**kwargs).all()
    # I was originally closing the session here, but that makes it impossible for the loaded objects to do
    # any additional lazy loading of their relationships
    return result


def fetch_one(cls, **kwargs):
    return load_session.query(cls).filter_by(**kwargs).one()


def fetch_as_dict(cls, **kwargs):
    return {obj.id: obj for obj in fetch(cls, **kwargs)}


def models_to_lookup(models):
    """
    Takes a ilst of SQLAlchemy models (from a query or relationship) and returns a dictionary with the id and name of
    each model object
    """
    return {obj.id: obj.name for obj in models}


def fetch_as_lookup(cls, **kwargs):
    return models_to_lookup(fetch(cls, **kwargs))


def fetch_as_df(cls):
    # ignore the primary key column since it is not interesting for dataframe purposes
    cols = [column.key for column in cls.__mapper__.columns.values() if column.key != 'id']

    # Note: at this stage parent_id is the only index column, since that is what DataMapper will be
    # using to select slices from the whole-table DataFrame for each individual parent object. It is tempting
    # to set up all the non-"value" columns as indexes here since we know they will ultimately be used
    # that way, but if we do that many of them will become float indexes rather than int indexes because
    # they will contain some NULL/NaN values. (pandas int columns don't support NaN, so columns with NaN
    # that would otherwise be int are coerced to float.) Instead, we delay setting indices until
    # DataMapper pulls its individual slices.
    # TODO: (MAC) remove schema= specification here once migration is complete
    return pd.read_sql_table(cls.__tablename__, engine, schema='migrated', columns=cols, index_col='parent_id').sort_index()


def fetch_column(col, **kwargs):
    """
    Returns the values from a single column as a list. col is expected to be something like DemandDrivers.id
    """
    return [row[0] for row in fetch(col, **kwargs)]


def get(cls, id_):
    """
    Essentially provides a passthrough to SQLAlchemy's get() method to get a single object by primary key
    while using SQLAlchemy's identity map to avoid redundant queries
    """
    return load_session.query(cls).get(id_)


def session():
    new_session = MakeSession()
    # TODO: (MAC) remove this once migration is complete; it's needed for some low-level queries while we are migrating
    new_session.execute("SET search_path TO migrated")
    return new_session
